# install
mkdir dev
cd ~/dev
sudo apt-get update
sudo apt-get install build-essential
sudo apt-get install clang-3.5 llvm
sudo ln -s /usr/bin/clang-3.5 /usr/bin/clang
sudo ln -s /usr/bin/clang++-3.5 /usr/bin/clang++
sudo apt-get install g++
sudo apt-get install make
sudo apt-get install libboost-all-dev
sudo apt-get install git
git clone https://github.com/JohnLangford/vowpal_wabbit.git
cd vowpal_wabbit
make
sudo make install

# 1M
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings.dat > ratings_t.dat
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache
awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < ratings_t.dat > tmp_a
awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b
awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' tmp_a tmp_b > matrix_t.dat
rm tmp_a tmp_b
vw -d matrix_dat -i movielens.reg -t -p predictions.txt
tail -n +4000 predictions_t.dat | head -n 4000 | grep '|u 2' | awk '{printf "%f %s %d %s %d\n", $5, $1, $2, $3, $4}' | sort -nr | head



# 20M
tail -n +2 ratings.csv | awk -F"," '{printf "%d |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat #56s
tail -n +2 movies.csv | awk -F"," '{printf "|i %d\n", $1}' > movies_t.dat #1s
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat #10s
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache #3m13s
awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < ratings_t.dat > tmp_a #46s
awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b #32m47s

rm matrix_t.dat
h=$((4000 * 27278))  # 20000 users per round with 27278 movies per user
for i in `seq 0 32`; do  # 33 rounds of 4200 will do all 138493 users. We do rounds to avoid using all the RAM.
  t=$(($i*$h))
  echo "doing $i/32 - from $t to $(($t+$h))"
  tail -n +$t tmp_b | head -n $h > tmp_c
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' tmp_a tmp_c >> matrix_t.dat
  date
done
rm tmp_a tmp_b tmp_c
# 1h45m?

vw -d matrix_t.dat -i movielens.reg -t -p predictions.txt # 40m22s

paste -d " " predictions.txt matrix_t.dat > predictions_t.dat
rm predictions.txt matrix_t.dat
# 1m10s

generate_recs() {
  local t=$(($1*27000))
  echo "User $(($1+1))/138493"
  tail -n +$t predictions_t.dat | head -n 50000 | grep "|u $(($i+1))" | sort -nr | head >> $2
}
for i in `seq 0 10000`; do generate_recs recs_1.dat; date; done # 138493 users
rm predictions_t.dat
# ?m?s

# $X (X hours @ $0.33 cents per hour) for EC2 and $0.67 ($0.003 per GB-day for 200GB for 1 day) for disk space. --> $X + $0.67
