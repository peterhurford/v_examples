# Convert ratings from movielens format to VW format (3s)
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings.dat > ratings_t.dat

# Convert movie data from movielens format to VW format (0s)
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat

# Create a user dataset for VW from the unique customer ids in the ratings dataset (0s)
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat

# Train a VW ALS model on the data (30s)
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache

# Create a user-product grid for all the possible user-product combinations (18s)
awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b

# Remove the rating to get raw user-product combinations present in the ratings (2s)
awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < ratings_t.dat > tmp_a

# Split grid into eight sub-grids (1s)
gsplit -d --number 8 tmp_b tmp_b
gsplit -d --number 8 tmp_a tmp_a

generate_matrix() {
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' "tmp_a0$1" "tmp_b0$1" > "matrix_t_0$1"
  vw -d "matrix_t_0$1" -i movielens.reg -t -p "predictions$1.txt"         # Predict
  paste -d " " "predictions$1.txt" "matrix_t_0$1" > "predictions_$1.dat"  # Add labels
  rm "matrix_t_0$1" "predictions$1.txt"                                   # Remove files
  echo "Finished matrix $1 on `date`"
}
date; for i in `seq 0 7`; do generate_matrix $i &
done
# 1m11s

generate_recs() {
  sort -nr -k3 -k1 "predictions_$1.dat" | awk '{ if(!($3 in seen)) { seen[$3] = 1; for (i=0; i<10; i++) { print; getline } } }' > "recs_$1.dat"
  echo "Finished recs $1 on `date`"
}
date; for i in `seq 0 7`; do generate_recs $i &
done
# 12s

cat recs* > all_recs_s.dat # 0s
awk '{ if(!($3 in seen)) { seen[$3] = 1; for (i=0; i<8; i++) { print; getline }; print; getline; print } }' all_recs_s.dat > all_recs.dat #0s
wc -l all_recs.dat

# TOTAL: 2m17s
# Done on my laptop (16G RAM 8 core Macbook Pro Mid-2015), so no cost data.
