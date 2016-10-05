# Convert ratings from movielens format to VW format (58s r3.8xlarge time)
tail -n +2 ratings.csv | awk -F"," '{printf "%f |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat

# Convert movie data from movielens format to VW format (0s)
tail -n +2 movies.csv | awk -F"," '{printf "|i %d\n", $1}' > movies_t.dat

# Create a user dataset for VW from the unique customer ids in the ratings dataset (5s)
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat

# Train a VW ALS model on the data (1m35s)
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache

# r3.8xlarge: Create splits for generating grids (2s)
split -d -l 17312 users_t.dat users  # 138493 users into 8 splits
split -d -l 3410 movies_t.dat movies   # 27278 movies into 8 splits
split -d -l 2500033 ratings_t.dat ratings # 20000263 ratings into 8 splits

generate_matrix() {
  awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < "ratings0$2" > "tmp_a_$2"
  awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' "movies0$1" "users0$2" > "tmp_b_$1_$2"
  echo "Finished matrix $1 x $2 on `date`"
}
date; for i in `seq 0 7`; do  # 3m13s
  for j in `seq 0 7`; do
    generate_matrix $i $j &
  done
done

trim_matrix() {
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' "tmp_a_$2" "tmp_b_$1_$2" > "matrix_t_$1_$2"
  echo "Finished matrix $1 x $2 on `date`"
}
trim_multiple_matricies() {
  for j in `seq 0 7`; do
    trim_matrix $1 $j  # Cannot parallelize further due to RAM limitations
  done
}
date; for i in `seq 0 7`; do  # 15m18s
  trim_multiple_matricies $i &
done

predict_matrix() {
  vw -d "matrix_t_$1_$2" -i movielens.reg -t -p "predictions_$1_$2.txt"
  paste -d " " "predictions_$1_$2.txt" "matrix_t_$1_$2" > "predictions_$1_$2.dat"
  echo "Finished matrix $1 x $2 on `date`"
}
date; for i in `seq 0 7`; do # 54m17s
  for j in `seq 0 7`; do
    predict_matrix $i $j &
  done
done

# Turn predictions into top 10 recs per user
generate_recs() {
  sort -nr -k3 -k1 "predictions_$1_$2.dat" | awk '{ if(!($3 in seen)) { seen[$3] = 1; for (i=0; i<10; i++) { print; getline } } }' > "recs_$1_$2.dat"
  echo "Finished recs $1 x $2 on `date`"
}
date; for i in `seq 0 7`; do # 12m41s
  for j in `seq 0 7`; do
    generate_recs $i $j &
  done
done

cat recs* > all_recs_s.dat #1s
sort -nr -k3 -k1 all_recs_s.dat | awk '{ if(!($3 in seen)) { seen[$3] = 1; for (i=0; i<8; i++) { print; getline }; print; getline; print } }' > all_recs.dat #4s
wc -l all_recs.dat

# TOTAL: 1h28m14s on r3.8xlarge (244G RAM 32 core)
