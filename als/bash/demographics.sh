# Convert ratings from movielens format to VW format
awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}' < ratings.dat > ratings_t.dat # 1000209

# Convert movie data from movielens format to VW format
awk -F"::" '{printf "|i %d\n", $1}' < movies.dat > movies_t.dat

# Convert user data from movielens format to VW format, using gender data
awk -F"::" {'if ($2=="F") { print "|u", $1, "|g F:1" } else { print "|u", $1, "|g F:0"}}' < users.dat > users_t.dat

# Add user data to ratings data
join -1 2 -2 3 -a1 -e0 -o'2.1,2.2,2.3,2.4,2.5,1.3,1.4' users_t.dat ratings_t.dat > ratings_tt.dat

# Make training set and test set
head -n 80167 ratings_t.dat | gshuf > train.dat
tail -n 20042 ratings_t.dat > test.dat
head -n 80167 ratings_tt.dat | gshuf > train_d.dat
tail -n 20042 ratings_tt.dat > test_d.dat
sed "s/|g //" train_d.dat > train_d2.dat  # Include gender as part of the item matrix, see http://www.eumssi.eu/wp-content/uploads/2013/11/PID3064447.pdf
sed "s/|g //" test_d.dat > test_d2.dat

# Train a VW ALS model on the train data
vw -d train.dat -b 24 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 20 --decay_learning_rate 0.97 --power_t 0 -f movielens.reg --cache_file movielens.cache; vw test.dat -i movielens.reg -t -p predictions.txt
# Average Loss: 0.985515
vw -d train_d.dat -b 24 -q ui -q gi --rank 10 --l2 0.001 --learning_rate 0.015 --passes 20 --decay_learning_rate 0.97 --power_t 0 -f movielens_d.reg --cache_file movielens_d.cache; vw test_d.dat -i movielens_d.reg -t -p predictions_d.txt
# Average Loss: 1.015805
vw -d train_d.dat -b 24 -q ui -q gi -q ug --rank 10 --l2 0.001 --learning_rate 0.015 --passes 20 --decay_learning_rate 0.97 --power_t 0 -f movielens_d3.reg --cache_file movielens_d.cache; vw test_d.dat -i movielens_d3.reg -t -p predictions_d3.txt
# Average Loss: 1.020143
vw -d train_d2.dat -b 24 -q ui --rank 10 --l2 0.001 --learning_rate 0.015 --passes 20 --decay_learning_rate 0.97 --power_t 0 -f movielens_d2.reg --cache_file movielens_d2.cache; vw test_d2.dat -i movielens_d2.reg -t -p predictions_d2.txt
# average loss = 1.003438
