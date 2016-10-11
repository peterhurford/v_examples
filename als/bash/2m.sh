# Subset dat
head -n 2000001 ratings.csv > ratings_.csv # Cut ratings to go to 2M, include header

# Convert ratings from movielens format to VW format (5s)
tail -n +2 ratings_.csv | awk -F"," '{printf "%f |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat

# Convert movie data from movielens format to VW format (0s)
tail -n +2 movies.csv | awk -F"," '{printf "|i %d\n", $1}' > movies_t.dat

# Create a user dataset for VW from the unique customer ids in the ratings dataset (1s)
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat

# Train a VW ALS model on the data (11s)
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache
# Tue Oct 11 18:48:01 UTC 2016
# Tue Oct 11 18:48:12 UTC 2016

# Create splits for generating grids (0s)
split -d -l 3392 users_t.dat users  # 13567 users into 4 splits
split -d -l 6820 movies_t.dat movies   # 27278 movies into 4 splits
split -d -l 500000 ratings_t.dat ratings # 2000000 ratings into 4 splits

generate_matrix() {
  awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < "ratings0$2" > "tmp_a_$2"
  awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' "movies0$1" "users0$2" > "tmp_b_$1_$2"
  echo "Finished matrix $1 x $2 on `date`"
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    generate_matrix $i $j &
  done
done
# 24s

trim_matrix() {
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' "tmp_a_$2" "tmp_b_$1_$2" > "matrix_t_$1_$2"
  echo "Finished matrix $1 x $2 on `date`"
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    trim_matrix $i $j
  done
done
# 5m2s

predict_matrix() {
  vw -d "matrix_t_$1_$2" -i movielens.reg -t -p "predictions_$1_$2.txt"
  paste -d " " "predictions_$1_$2.txt" "matrix_t_$1_$2" > "predictions_$1_$2.dat"
  echo "Finished matrix $1 x $2 on `date`"
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    predict_matrix $i $j &
  done
done
# 15m24s

# Turn predictions into top 10 recs per user (20m12s)
generate_recs() {
  sort -nr -k3 -k1 "predictions_$1_$2.dat" | awk '{ if(!($3 in seen)) { seen[$3] = 1; for (i=0; i<10; i++) { print; getline } } }' > "recs_$1_$2.dat"
  echo "Finished recs $1 x $2 on `date`"
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    generate_recs $i $j   # Parallelizing this seems to run into RAM problems?
  done
done
# 3m33s

cat recs* > all_recs_s.dat #0s
sort -nr -k3 -k1 all_recs_s.dat | awk '{ if(!($3 in seen)) { seen[$3] = 1; for (i=0; i<8; i++) { print; getline }; print; getline; print } }' > all_recs.dat #0s
wc -l all_recs.dat

# TOTAL: 24m42s
# Done on c3.4xlarge (30G RAM 16 core)
