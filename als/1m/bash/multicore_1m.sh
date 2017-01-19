if [[ $# -gt 1 ]]; then
  if [[ $1 == '--cores' ]]; then
    cores=$2
  else
    cores=4
  fi
else
  cores=4
fi

echo "File processing..."
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < als/1m/data/ratings.dat > als/1m/data/ratings_t.dat
awk -F"::" '{printf "|i %d\n", $1}' < als/1m/data/movies.dat > als/1m/data/movies_t.dat
awk '{print $3}' < als/1m/data/ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > als/1m/data/users_t.dat
gshuf als/1m/data/ratings_t.dat > als/1m/data/ratings_ts.dat

ratings_count=$(wc -l 'als/1m/data/ratings_ts.dat' | awk {'print $1'})
train_count=$(echo "$ratings_count*0.8" | bc -l | awk '{printf("%d\n",$0+=$0<0?0:0.9)}')
test_count=$(echo "$ratings_count*0.2" | bc -l | awk '{printf("%d\n",$0+=$0<0?0:0.9)}')
train_core_count=$(echo "$train_count/$cores" | bc -l | awk '{printf("%d\n",$0+=$0<0?0:0.9)}')
test_core_count=$(echo "$test_count/$cores" | bc -l | awk '{printf("%d\n",$0+=$0<0?0:0.9)}')

gsplit -d -l $train_count als/1m/data/ratings_ts.dat
mv x00 als/1m/data/ratings_train.dat
mv x01 als/1m/data/ratings_test.dat
gsplit -d -l $train_core_count als/1m/data/ratings_train.dat als/1m/data/ratings_train_
gsplit -d -l $test_core_count als/1m/data/ratings_test.dat als/1m/data/ratings_test_
learner() {
  vw --total $cores --node $1 --unique_id 0 --span_server localhost --holdout_off -d "als/1m/data/$2_0$1" -f "als/1m/data/model.$1" --cache_file "als/1m/data/cachefile.$1" --passes 10 -b 21 -q ui --rank 10 --l2 0.01 --learning_rate 0.015 --decay_learning_rate 0.97 --power_t 0
}
predictor() {
  vw --total $cores --node $1 --unique_id 0 --span_server localhost --holdout_off -d "als/1m/data/$2_0$1" -i als/1m/data/model -t -p "als/1m/data/$2_preds0$1"
  paste -d " " "als/1m/data/$2_0$1" "als/1m/data/$2_preds0$1" >  "als/1m/data/$2_preds0$1_t"
}

echo "Provisioning $cores cores for $ratings_count ratings (train $train_count with $train_core_count per core, test $test_count with $test_core_count per core)..."
spanning_tree
for i in `seq 0 $(($cores-1))`; do
  learner $i ratings_train &
done
wait
echo "Testing..."
mv als/1m/data/model.0 als/1m/data/model
for i in `seq 0 $(($cores-1))`; do
  predictor $i ratings_test &
done
wait
killall spanning_tree
cat als/1m/data/ratings_test_preds*_t > als/1m/data/preds
printf "RMSE: "
awk '{ $7 = ($6 - $1)^2 } 1' als/1m/data/preds | awk '{s+=$7} END {print (s/200041)^0.5}'

echo "Cleaning..."
rm als/1m/data/model*
rm als/1m/data/cachefile*
rm als/1m/data/*preds*
rm als/1m/data/*_t
rm als/1m/data/*_t*.dat
rm als/1m/data/ratings_train*
rm als/1m/data/ratings_test*
