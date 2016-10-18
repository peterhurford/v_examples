date
if [[ $# -gt 1 ]]; then
  if [[ $1 == '--cores' ]]; then
    cores=$2
  else
    cores=4
  fi
else
  cores=4
fi

echo "Cleaning..."
rm model*
rm cachefile*
rm *preds*
rm *_t
rm *_t*.dat
rm ratings_train*
rm ratings_test*

echo "File processing..."
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings.dat > ratings_t.dat
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat
gshuf ratings_t.dat > ratings_ts.dat

ratings_count=$(wc -l 'ratings_ts.dat' | awk {'print $1'})
train_count=$(echo "$ratings_count*0.8" | bc -l | awk '{printf("%d\n",$0+=$0<0?0:0.9)}')
test_count=$(echo "$ratings_count*0.2" | bc -l | awk '{printf("%d\n",$0+=$0<0?0:0.9)}')
train_core_count=$(echo "$train_count/$cores" | bc -l | awk '{printf("%d\n",$0+=$0<0?0:0.9)}')
test_core_count=$(echo "$test_count/$cores" | bc -l | awk '{printf("%d\n",$0+=$0<0?0:0.9)}')

gsplit -d -l $train_count ratings_ts.dat
mv x00 ratings_train.dat
mv x01 ratings_test.dat
gsplit -d -l $train_core_count ratings_train.dat ratings_train_
gsplit -d -l $test_core_count ratings_test.dat ratings_test_
learner() {
  vw --total $cores --node $1 --unique_id 0 --span_server localhost --holdout_off -d "$2_0$1" -f model.$1 --cache_file cachefile.$1 --passes 80 -b 18 -q ui --rank 20 --l2 0.01 --learning_rate 0.015 --decay_learning_rate 0.97 --power_t 0
}
predictor() {
  vw --total $cores --node $1 --unique_id 0 --span_server localhost --holdout_off -d "$2_0$1" -i model -t -p "$2_preds0$1"
  paste -d " " "$2_0$1" "$2_preds0$1" >  "$2_preds0$1_t"
}

echo "Provisioning $cores cores for $ratings_count ratings (train $train_count with $train_core_count per core, test $test_count with $test_core_count per core)..."
spanning_tree
for i in `seq 0 $(($cores-1))`; do
  learner $i ratings_train &
done
wait
echo "Testing..."
mv model.0 model
for i in `seq 0 $(($cores-1))`; do
  predictor $i ratings_test &
done
wait
killall spanning_tree
cat ratings_test_preds*_t > preds
printf "RMSE: "
awk '{ $7 = ($6 - $1)^2 } 1' preds | awk '{s+=$7} END {print (s/200041)^0.5}'
date
