# Convert ratings from movielens format to VW format (28s)
tail -n +2 ratings.csv | awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat   
tail -n +2 ratings.csv | awk -F"," '{printf "%f |u %d |i %d\n", $3, $1, $2}' > ratings_t.dat # 20000263 ratings
# Convert movie data from movielens format to VW format (0s)
tail -n +2 movies.csv | awk -F"::" '{printf "|i %d\n", $1}' > movies_t.dat                      # 27278 movies

# Create a user dataset for VW from the unique customer ids in the ratings dataset (4s)
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat            # 138493 users

# Train a VW ALS model on the data (3m11s)
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache

# Create a user-product grid for all the possible user-product combinations (6m45s)
split -dl 34624 users_t.dat users  # 138493 users into four sections
split -dl 6820 movies_t.dat movies # 27278 movies into four sections (4x4 sections = 16 matricies for 16 cores)
merge_grid() {
    awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' "movies0$1" "users0$2" > "tmp_b_$1_$2"
    echo "Finished $1 x $2 on `date`"
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    merge_grid $i $j &
  done
done

# Predict on each grid (2h15m34s)
generate_matrix() {
  vw -d "tmp_b_$1_$2" -i movielens.reg -t -p "predictions$1_$2.txt"            # Predict
  paste -d " " "predictions$1_$2.txt" "tmp_b_$1_$2" > "predictions_$1_$2.dat"  # Add labels
  rm "tmp_b_$1_$2" "predictions$1_$2.txt"                                      # Remove files
  echo "Finished matrix $1 x $2 on `date`"
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    generate_matrix $i $j &
  done
done

# Remove the rating to get raw user-product combinations present in the ratings and sort (4s)
cat ratings_t.dat | parallel --pipe "awk '{print \$2, \$3, \$4, \$5}'" > tmp_a

# Split into subfiles (2s)
split -dl 5000066 tmp_a tmp_a  # 20000263 ratings / 4 splits (TODO: See if we can get it so this can match up with 16 splits, perhaps with doing tmp_b by movie instead of by user?)

# Get top 10 recommendations for each user (7m39s?)
generate_recs() {
  # Split prediction file by user (27278 predictions per user)
  split -dl 27278 "predictions_$1_$2.dat" "recs_$1_$2_"
  for i in `seq 0 1704`; do # (users x movies / 16) / users - 1
    if [ $i -ge 9900 ]
      then i=$(($i-9900+990000))
    elif [ $i -ge 90 ]
      then i=$(($i-90+9000))
    elif [ $i -lt 10 ]
      then i="0$i"
    fi
    rm "predictions_$1_$2.dat"
    sort -nr "recs_$1_$2_$i" | head -n 500 | awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' | comm -2 -3 - "tmp_a$1" | head > "recs_t_$1_$2_$i"
    echo "Finished grid $1 x $2, user $i on `date`"
  done
}
date; for i in `seq 0 3`; do
  for j in `seq 0 3`; do
    generate_recs $i $j &
  done
done
# Fri Sep 30 21:03:32 UTC 2016

echo recs_t_* | xargs cat > all_recs.dat # 4s
rm recs* #1s
wc -l all_recs.dat

# TOTAL: 3m23s on a c4.4xlarge
