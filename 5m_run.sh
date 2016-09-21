# Cut ratings in half to go to 2M
head -n 2000001 ratings.csv > ratings_.csv

tail -n +2 ratings_.csv | awk -F"," '{printf "%f |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat #5s
tail -n +2 movies.csv | awk -F"," '{printf "|i %d\n", $1}' > movies_t.dat #0s

awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat #1s, 13567 users
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache #12s
cat ratings_t.dat | parallel --pipe "awk '{print \$2, \$3, \$4, \$5}'" | cat > tmp_a #1s
# Group: 12s

awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b #3m5s
rm movielens.cache ratings.csv ratings_t.dat

make_matrix() {
  local h=$((2000 * 27278))  # 2000 users per round with 27278 movies per user
  local t=$(($1*$h))
  echo "doing $1/6 - from $t to $(($t+$h))"
  local source_file="tmp_c_$1"
  local matrix_file="matrix_t_$1.dat"
  tail -n +$t tmp_b | head -n $h > $source_file
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' tmp_a $source_file > $matrix_file
  rm $source_file
  echo "$1/6 complete on `date`"
}
date; for i in `seq 0 6`; do make_matrix $i &  # 7 rounds of 2000 will do all 13567 users. We do rounds to avoid using all the RAM.
done
rm tmp_*
#2m11s

predict_on_matrix() {
  vw -d "matrix_t_$1.dat" -i movielens.reg -t -p "predictions_$1.txt"
  paste -d " " "predictions_$1.txt" "matrix_t_$1.dat" > "predictions_t_$1.dat"
  rm "predictions_$1.txt" "matrix_t_$1.dat"
  echo "Finished predicting on matrix $1/6 on `date`"
}
date; for i in `seq 0 6`; do
  echo "Scheduling predict on matrix $i/6"
  predict_on_matrix $i &
done
#11m20s

generate_recs() {
  local user=$(($2+1))
  local line=`grep -m 1 -nF "|u $user " "predictions_t_$1.dat" | awk -F":" '{print $1}'`
  tail -n +$line "predictions_t_$1.dat" | head -n 27278 | grep "|u $user " | sort -nr | head > "recs_$2.dat"
  echo "Finished recs for user $user/13567 on `date`"
}
generate_recs_section() {
  for j in `seq $(($1*2000)) $(($1*2000+1999))`; do
    generate_recs $1 $j
  done
}
date; for i in `seq 0 6`; do
  generate_recs_section $i &
done
# Wed Sep 21 19:01:35 UTC 2016

echo recs_*.dat | xargs cat > all_recs.dat
rm recs_*.dat
# TBD

# $0.11 (0.25 hours @ $0.67 cents per hour) for EC2 and $0.01 ($0.003 per GB-day for 200GB for 0.01 day) for disk space. --> $0.12
