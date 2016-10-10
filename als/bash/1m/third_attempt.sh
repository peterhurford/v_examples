# Convert ratings from movielens format to VW format (3s)
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings.dat > ratings_t.dat

# Convert movie data from movielens format to VW format (0s)
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat

# Create a user dataset for VW from the unique customer ids in the ratings dataset (0s)
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat

# Train a VW ALS model on the data (8s)
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache

# Create splits for generating grids (0s)
split -d -l 1510 users_t.dat users  # 6040 users into 4 splits
split -d -l 971 movies_t.dat movies   # 3883 movies into 4 splits
split -d -l 62514 ratings_t.dat ratings # 1000209 ratings into 16 splits

# Generate predictions (1m3s)
generate_matrix() {
  mult=$(( $1 * $2 ))
  if [ $mult -lt 10 ]; then r="0$mult"; else r="$mult"; fi  # Get correct file index
  awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < "ratings$r" > "tmp_a_$1_$2"  # Make a list of unlabeled ratings
  awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' "movies0$1" "users0$2" > "tmp_b_$1_$2"  # Get all user-product combinations
  awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' "tmp_a_$1_$2" "tmp_b_$1_$2" > "matrix_t_$1_$2"  # Subtract out unlabeled ratings, getting only novel user-product combinations
  vw -d "matrix_t_$1_$2" -i movielens.reg -t -p "predictions_$1_$2.txt" # Predict with model
  paste -d " " "predictions_$1_$2.txt" "matrix_t_$1_$2" > "predictions_$1_$2.dat" # Relabel predictions
  echo "Finished matrix $1 x $2 on `date`"
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    generate_matrix $i $j &
  done
done

# Turn predictions into top 10 recs per user (3s)
generate_recs() {
  # Sort recs by user and then score, then take top 10 recs for each user
  sort -nr -k3 -k1 "predictions_$1_$2.dat" | awk '{ if(!($3 in seen)) { seen[$3] = 1; for (i=0; i<10; i++) { print; getline } } }' > "recs_$1_$2.dat"
  echo "Finished recs $1 x $2 on `date`"
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    generate_recs $i $j &
  done
done

# Combine recs into one file (0s)
cat recs* > all_recs_s.dat

# Sometimes users can be duplicated across files (maybe not anymore?) so we clean the file again (0s)
awk '{ if(!($3 in seen)) { seen[$3] = 1; for (i=0; i<8; i++) { print; getline }; print; getline; print } }' all_recs_s.dat > all_recs.dat

wc -l all_recs.dat

# TOTAL: 1m17s on on c3.4xlarge (30G RAM 16 core)

# Bonus -- convert user-product row format to user-products<list> format (0s)
awk '{ if(!($3 in seen)) { seen[$3] = 1; printf "[%d, [", $3; for (i=0; i<9; i++) { printf "%d, ", $5; getline }; printf "%d]]\n", $5 } }' all_recs.dat > rec_list.dat
