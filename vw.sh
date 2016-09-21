# install
mkdir dev; cd ~/dev
sudo apt-get update
sudo apt-get install build-essential
sudo apt-get install clang-3.5 llvm
sudo ln -s /usr/bin/clang-3.5 /usr/bin/clang; sudo ln -s /usr/bin/clang++-3.5 /usr/bin/clang++
sudo apt-get install libboost-all-dev
sudo apt-get install git
git clone https://github.com/JohnLangford/vowpal_wabbit.git
cd vowpal_wabbit
make
sudo make install
cd ..

# 1M
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings.dat > ratings_t.dat #3s
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat #0s
# Group: 3s

awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat #0s
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache #8s
awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < ratings_t.dat > tmp_a #3s
awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b #10s
awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' tmp_a tmp_b > matrix_t.dat #17s
# Group: 17s

rm tmp_a tmp_b
vw -d matrix_t.dat -i movielens.reg -t -p predictions.txt #1m58s

paste -d " " predictions.txt matrix_t.dat > predictions_t.dat #2s

generate_recs() {
  local t=$(($1*3000))
  local user=$(($1+1))
  local line=`grep -m 1 -nF "|u $user " predictions_t.dat | awk -F":" '{print $1}'`
  tail -n +$line predictions_t.dat | head -n 3882 | grep "|u $user " | sort -nr | head > "recs_$1.dat"
  echo "Finished recs for user $user/6039 on `date`"
}
date; for i in `seq 0 6039`; do generate_recs $i &
done
echo recs_*.dat | xargs cat > all_recs.dat
rm recs_*.dat
# 7m39s

# 9m59s

# TOTAL: 9m59s
# $0.12 (0.17 hours @ $0.67 cents per hour) for EC2 and $0.01 ($0.003 per GB-day for 200GB for 0.01 day) for disk space. --> $0.13


# 20M
tail -n +2 ratings.csv | awk -F"," '{printf "%f |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat #60s
tail -n +2 movies.csv | awk -F"," '{printf "|i %d\n", $1}' > movies_t.dat #0s
# Group: 60s

awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat #6s
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache #1m43s
cat ratings_t.dat | parallel --pipe "awk '{print \$2, \$3, \$4, \$5}'" | cat > tmp_a #7s
# Group: 1m43s

awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b #32m15s
rm movielens.cache ratings.csv ratings_t.dat

make_matrix() {
  local h=$((10000 * 27278))  # 10000 users per round with 27278 movies per user
  local t=$(($1*$h))
  echo "doing $1/13 - from $t to $(($t+$h))"
  local source_file="tmp_c_$1"
  local matrix_file="matrix_t_$1.dat"
  tail -n +$t tmp_b | head -n $h > $source_file
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' tmp_a $source_file > $matrix_file
  rm $source_file
  echo "$1/13 complete on `date`"
}
date; for i in `seq 0 13`; do make_matrix $i &  # 14 rounds of 10000 will do all 138493 users. We do rounds to avoid using all the RAM.
done
rm tmp_*
#1h30m13s
# Expected count: 1,846,960,613

predict_on_matrix() {
  vw -d "matrix_t_$1.dat" -i movielens.reg -t -p "predictions_$1.txt"
  paste -d " " "predictions_$1.txt" "matrix_t_$1.dat" > "predictions_t_$1.dat"
  rm "predictions_$1.txt" "matrix_t_$1.dat"
  echo "Finished predicting on matrix $1/13 on `date`"
}
date; for i in `seq 0 13`; do
  echo "Scheduling predict on matrix $i/13"
  predict_on_matrix $i &
done
# Wed Sep 21 03:13:45 UTC 2016

generate_recs() {
  local t=$(($2*20000))
  local user=$(($2+1))
  local line=`grep -m 1 -nF "|u $user " "predictions_t_$1.dat" | awk -F":" '{print $1}'`
  tail -n +$line "predictions_t_$1.dat" | head -n 27278 | grep "|u $user " | sort -nr | head > "recs_$2.dat"
  echo "Finished recs for user $user/138493 on `date`"
}
date; for i in `seq 0 13`; do
  for j in `seq $(($i*10000)) (($i*10000+9999))`; do
    generate_recs $i $j &
  done
done

echo recs_*.dat | xargs cat > all_recs.dat
rm recs_*.dat
# TBD

# $0.11 (0.25 hours @ $0.67 cents per hour) for EC2 and $0.01 ($0.003 per GB-day for 200GB for 0.01 day) for disk space. --> $0.12
