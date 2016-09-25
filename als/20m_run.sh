# ON ALL MACHINES
tail -n +2 ratings.csv | awk -F"," '{printf "%f |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat #54s
tail -n +2 movies.csv | awk -F"," '{printf "|i %d\n", $1}' > movies_t.dat #0s

awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat #5s, 138493 users
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache #1m26s
cat ratings_t.dat | parallel --pipe "awk '{print \$2, \$3, \$4, \$5}'" | cat > tmp_a #4s

# MACHINE A
split -l 34624 users_t.dat; rm users_t.dat; rm xab xac xad; mv xaa users_t.dat #0s

# MACHINE B
split -l 34624 users_t.dat; rm users_t.dat; rm xaa xac xad; mv xab users_t.dat

# MACHINE C
split -l 34624 users_t.dat; rm users_t.dat; rm xaa xab xad; mv xac users_t.dat

# MACHINE D
split -l 34624 users_t.dat; rm users_t.dat; rm xaa xab xac; mv xad users_t.dat

# ON EACH MACHINE
awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b #7m30s

make_matrix() {
  local h=$((2164 * 27278))  # 2164 users per round with 27278 movies per user
  local t=$(($1*$h))
  echo "doing $1/15 - from $t to $(($t+$h))"
  local source_file="tmp_c_$1"
  local matrix_file="matrix_t_$1.dat"
  tail -n +$t tmp_b | head -n $h > $source_file
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' tmp_a $source_file > $matrix_file
  rm $source_file
  echo "$1/15 complete on `date`"
}
date; for i in `seq 0 15`; do make_matrix $i  # 16 rounds of 2164 will do all 34624 users per machine. We do rounds to avoid using all the RAM.
done
#20m34s

predict_on_matrix() {
  vw -d "matrix_t_$1.dat" -i movielens.reg -t -p "predictions_$1.txt"
  paste -d " " "predictions_$1.txt" "matrix_t_$1.dat" > "predictions_t_$1.dat"
  rm "predictions_$1.txt" "matrix_t_$1.dat"
  echo "Finished predicting on matrix $1/15 on `date`"
}
date; for i in `seq 0 15`; do
  echo "Scheduling predict on matrix $i/15"
  predict_on_matrix $i &
done
# 21m18s

generate_recs() {
  local user=$(($2+$3))
  local line=`grep -m 1 -nF "|u $user " "predictions_t_$1.dat" | awk -F":" '{print $1}'`
  tail -n +$line "predictions_t_$1.dat" | head -n 27278 | grep "|u $user " | sort -nr | head > "recs_$2.dat"
  echo "Finished recs for user $user/$4 on `date`"
}

# MACHINE A
generate_recs_section() {
  for j in `seq $(($1*2164)) $(($1*2164+2163))`; do
    generate_recs $1 $j 1 34624
  done
}

# MACHINE B
generate_recs_section() {
  for j in `seq $(($1*2164)) $(($1*2164+2163))`; do
    generate_recs $1 $j 34625 69248
  done
}

# MACHINE C
generate_recs_section() {
  for j in `seq $(($1*2164)) $(($1*2164+2163))`; do
    generate_recs $1 $j 69249 103872
  done
}

# MACHINE D
generate_recs_section() {
  for j in `seq $(($1*2164)) $(($1*2164+2163))`; do
    generate_recs $1 $j 103873 138493
  done
}

# EACH MACHINE
date; for i in `seq 0 15`; do
  generate_recs_section $i &
done
# 1h1m11s

echo recs_*.dat | xargs cat > all_recs.dat
rm recs_*.dat
# 0s

# 1h53m2s
# $6.31 (1.88 hours @ $0.84*4 cents per hour for 4x c3.4xlarge) for EC2 and $0.17 ($0.003 per GB-day for 4x200GB for 0.07 day) for disk space. --> $6.48
