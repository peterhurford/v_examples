# ON ALL MACHINES
head -n 5000001 ratings.csv > ratings_.csv # Cut ratings to go to 5M, include header
tail -n +2 ratings_.csv | awk -F"," '{printf "%f |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat #14s
tail -n +2 movies.csv | awk -F"," '{printf "|i %d\n", $1}' > movies_t.dat #0s

awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat #1s, 34395 users
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache #25s
cat ratings_t.dat | parallel --pipe "awk '{print \$2, \$3, \$4, \$5}'" | cat > tmp_a #1s

# MACHINE A
split -l 8599 users_t.dat; rm users_t.dat; rm xab xac xad; mv xaa users_t.dat #0s, 8599 users per machine

# MACHINE B
split -l 8599 users_t.dat; rm users_t.dat; rm xaa xac xad; mv xab users_t.dat

# MACHINE C
split -l 8599 users_t.dat; rm users_t.dat; rm xaa xab xad; mv xac users_t.dat

# MACHINE D
split -l 8599 users_t.dat; rm users_t.dat; rm xaa xab xac; mv xad users_t.dat

# ON EACH MACHINE
awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b #1m52s

make_matrix() {
  local h=$((1075 * 27278))  # 1075 users per round with 27278 movies per user
  local t=$(($1*$h))
  echo "doing $1/7 - from $t to $(($t+$h))"
  local source_file="tmp_c_$1"
  local matrix_file="matrix_t_$1.dat"
  tail -n +$t tmp_b | head -n $h > $source_file
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' tmp_a $source_file > $matrix_file
  rm $source_file
  echo "$1/7 complete on `date`"
}
date; for i in `seq 0 7`; do make_matrix $i  # 8 rounds of 1075 will do all 8599 users per machine. We do rounds to avoid using all the RAM.
done
# 4m3s

predict_on_matrix() {
  vw -d "matrix_t_$1.dat" -i movielens.reg -t -p "predictions_$1.txt"
  paste -d " " "predictions_$1.txt" "matrix_t_$1.dat" > "predictions_t_$1.dat"
  rm "predictions_$1.txt" "matrix_t_$1.dat"
  echo "Finished predicting on matrix $1/7 on `date`"
}
date; for i in `seq 0 7`; do
  echo "Scheduling predict on matrix $i/7"
  predict_on_matrix $i &
done
# 5m5s

generate_recs() {
  local user=$(($2+$3))
  local line=`grep -m 1 -nF "|u $user " "predictions_t_$1.dat" | awk -F":" '{print $1}'`
  tail -n +$line "predictions_t_$1.dat" | head -n 27278 | grep "|u $user " | sort -nr | head > "recs_$2.dat"
  echo "Finished recs for user $user/$4 on `date`"
}

# MACHINE A
generate_recs_section() {
  for j in `seq $(($1*1075)) $(($1*1075+1074))`; do
    generate_recs $1 $j 1 8599
  done
}

# MACHINE B
generate_recs_section() {
  for j in `seq $(($1*1075)) $(($1*1075+1074))`; do
    generate_recs $1 $j 8600 17198
  done
}

# MACHINE C
generate_recs_section() {
  for j in `seq $(($1*1075)) $(($1*1075+1074))`; do
    generate_recs $1 $j 17199 25797
  done
}

# MACHINE D
generate_recs_section() {
  for j in `seq $(($1*1075)) $(($1*1075+1074))`; do
    generate_recs $1 $j 25798 34395
  done
}

# EACH MACHINE
date; for i in `seq 0 7`; do
  generate_recs_section $i &
done
# Thu Sep 22 15:01:03 UTC 2016
#15m10s

echo recs_*.dat | xargs cat > all_recs.dat
rm recs_*.dat
# 0s

#41m11s
# $2.32 (0.69 hours @ $0.84*4 cents per hour for 4x c3.4xlarge) for EC2 and $0.07 ($0.003 per GB-day for 4x200GB for 0.03 day) for disk space. --> $2.39
