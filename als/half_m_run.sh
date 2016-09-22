# Cut ratings in half to go to 0.5M (0s)
head -n 500000 ratings.dat > ratings_.dat

# Convert ratings from movielens format to VW format (1s)
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings_.dat > ratings_t.dat

# Convert movie data from movielens format to VW format (0s)
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat

# Create a user dataset for VW from the unique customer ids in the ratings dataset (0s)
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat

# Train a VW ALS model on the data (5s)
vw -d ratings_t.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache

# Remove the rating to get raw user-product combinations present in the ratings (1s)
awk '{printf "%s %d %s %d\n", $2, $3, $4, $5}' < ratings_t.dat > tmp_a

# Create a user-product grid for all the possible user-product combinations (5s)
awk 'FNR == NR { a[++n]=$0; next } { for(i=1; i<=n; i++) print $0, a[i] }' movies_t.dat users_t.dat > tmp_b

# Filter out the existing user-product combinations to only predict on novel combinations (8s)
awk 'NR == FNR { list[$0]=1; next } { if (! list[$0]) print }' tmp_a tmp_b > matrix_t.dat

# Remove unneeded files (0s)
rm tmp_a tmp_b

# Generate predictions for novel combinations (1m4s)
vw -d matrix_t.dat -i movielens.reg -t -p predictions.txt

# Add the user-product label to the predictions (1s)
paste -d " " predictions.txt matrix_t.dat > predictions_t.dat

# Get top 10 recommendations for each user (1m50s)
generate_recs() {
  local user=$(($1+1))
  local line=`grep -m 1 -nF "|u $user " predictions_t.dat | awk -F":" '{print $1}'`  # Get location of user.
  tail -n +$line predictions_t.dat | head -n 3882 | grep "|u $user " | sort -nr | head > "recs_$1.dat"  # Get all the ratings for the user, sort them, take top 10.
  echo "Finished recs for user $user/3069 on `date`"
}
date; for i in `seq 0 3069`; do generate_recs $i &  # For each user, generate recs.
done

# Combine user-specific recs into one file (0s)
echo recs_*.dat | xargs cat > all_recs.dat
rm recs_*.dat

# TOTAL: 3m24s
# $0.03 (0.06 hours @ $0.42 cents per hour) for EC2
