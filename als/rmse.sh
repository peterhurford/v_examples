# Convert ratings from movielens format to VW format
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings.dat > ratings_t.dat # 1000209

# Convert movie data from movielens format to VW format
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat

# Create a user dataset for VW from the unique customer ids in the ratings dataset
awk '{print $3}' < ratings_t.dat | uniq | awk '{printf "|u %d\n", $1}' > users_t.dat

# Make training set and test set
head -n 80167 ratings_t.dat > train.dat
tail -n 20042 ratings_t.dat > test.dat

# Train a VW ALS model on the train data
vw -d train.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache

# Test
vw test.dat -i movielens.reg -t -p predictions.txt
# Average Loss: 1.032852 (RMSE 1.016)

# Add the user-product label to the predictions
paste -d " " predictions.txt matrix_t.dat > predictions_t.dat

# Also manually calculate RMSE
awk '{print ($1-$2) ** 2}' predictions_t.dat | awk '{ SUM += $1} END { print SUM }' | awk '{print sqrt($1/20042)}'
# RMSE 1.01629

# ----

# Train a VW ALS model on the train data (try more passes)
rm movielens* predictions*
vw -d train.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 100 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache
# 54s

# Test
vw test.dat -i movielens.reg -t -p predictions.txt
# 1s, Average Loss: 0.990613 (RMSE 0.995)

# ----

# Train a VW ALS model on the train data (try other features)
rm movielens* predictions*
vw -d train.dat -b 24 --passes 100 -k --l2 1.25e-7 --lrq ui7 -f movielens.reg --cache_file movielens.cache
# 6s

# Test
vw test.dat -i movielens.reg -t -p predictions.txt
# 0s, Average Loss: 0.986698 (RMSE .993)
# ----

# Train a VW ALS model on the train data (try other features)
rm movielens* predictions*
vw -d train.dat -b 24 --passes 100 --l2 1.25e-6 --lrq ui14 --lrqdropout --power_t 0.5 -f movielens.reg --cache_file movielens.cache; vw test.dat -i movielens.reg -t -p predictions.txt
# 6s

# Test
vw test.dat -i movielens.reg -t -p predictions.txt
# 0s, Average Loss: 0.984641 (RMSE .992)

# ---
# Attempt to grid search (doesn't always produce the best results)
~/dev/vowpal_wabbit/utl/vw-hypersearch -L -t test.dat 1e-9 1e-4 vw -d train.dat -b 24 --passes 100 --l2 % --lrq ui14 --lrqdropout --power_t 0.5 -f movielens.reg --cache_file movielens.cache
