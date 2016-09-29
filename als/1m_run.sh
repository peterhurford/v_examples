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

# Split grid into eight sub-grids (1s)
gsplit -dl 2931665 tmp_b tmp_b  # 6040 users x 3883 movies / 8 splits = 2931665

generate_matrix() {
  vw -d "tmp_b0$1" -i movielens.reg -t -p "predictions$1.txt"         # Predict
  paste -d " " "predictions$1.txt" "tmp_b0$1" > "predictions_$1.dat"  # Add labels
  rm "tmp_b0$1" "predictions$1.txt"                                   # Remove files
  echo "Finished matrix $1 on `date`"
}
date; for i in `seq 0 7`; do generate_matrix $i &
done
# 1m8s

# Remove the rating to get raw user-product combinations present in the ratings and sort (13s)
awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < ratings_t.dat | sort > tmp_a
gsplit -dl 125026 tmp_a tmp_a  # 1000209 ratings / 8 splits

# Get top 10 recommendations for each user (7m39s)
generate_recs() {
  # Split prediction file by user (3883 predictions per user)
  gsplit -dl 3883 "predictions_$1.dat" "recs_$1_"
  for i in `seq 0 754`; do # (users x movies / 8) / users - 1
    if [ $i -lt 10 ]; then i="0$i"; fi
    if [ $i -ge 90 ]; then i=$(($i-90+9000)); fi
    sort -nr "recs_$1_$i" | head -n 500 | awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' | comm -2 -3 - "tmp_a0$1" | head > "recs_t_$1_$i"
    echo "Finished grid $1, user $i on `date`"
  done
}
date; for i in `seq 0 7`; do generate_recs $i &
done
# 1m5s

echo recs_t_* | xargs cat > all_recs.dat # 4s
rm recs* #1s
wc -l all_recs.dat

# TOTAL: 3m23s
# Done on my laptop (16G RAM 8 core Macbook Pro Mid-2015), so no cost data.
