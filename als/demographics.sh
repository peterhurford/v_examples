# Convert ratings from movielens format to VW format
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings.dat > ratings_t.dat # 1000209

# Convert movie data from movielens format to VW format
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat

# Convert user data from movielens format to VW format, using gender data
awk -F"::" {'if ($2=="F") { print "|u", $1, "|g F:1" } else { print "|u", $1, "|g F:0"}}' < users.dat > users_t.dat

# Add user data to ratings data
join -1 2 -2 3 -a1 -e0 -o'2.1,2.2,2.3,2.4,2.5,1.3,1.4' users_t.dat ratings_t.dat > ratings_tt.dat

# Make training set and test set
head -n 80167 ratings_t.dat > train.dat
tail -n 20042 ratings_t.dat > test.dat
head -n 80167 ratings_tt.dat > train_d.dat
tail -n 20042 ratings_tt.dat > test_d.dat

# Train a VW ALS model on the train data
vw -d train.dat -b 18 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache
vw -d train_d.dat -b 18 -q ui -q ug --rank 10 --l2 0.001 --learning_rate 0.015 --passes 5 --decay_learning_rate 0.97 --power_t 0 -f movielens_d.reg --cache_file movielens_d.cache

# Test
vw test.dat -i movielens.reg -t -p predictions.txt
# Average Loss: 1.019431
vw test_d.dat -i movielens_d.reg -t -p predictions_d.txt
# Average Loss: 1.022556
