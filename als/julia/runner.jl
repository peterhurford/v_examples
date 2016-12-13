#TODO: This code is very slow...

num_lines = 100000
then = now()
run(pipeline(`cat als/data/movies.dat`, `awk -F"::" '{printf "|i %d\n", $1}'`, "als/data/movies_t.dat"))
run(pipeline(`head -n $num_lines als/data/ratings.dat`, `gshuf`, "als/data/ratings_s.dat"))
ratings_count = parse(Int, split(readstring(`wc -l als/data/ratings_s.dat`))[1])
train_count = convert(Int, floor(ratings_count * 0.8))
run(`gsplit -d -l $train_count als/data/ratings_s.dat`)
run(`mv x00 als/data/ratings_train.dat`)
run(`mv x01 als/data/ratings_test.dat`)
run(pipeline(`cat als/data/ratings_train.dat`, `awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}'`, "als/data/ratings_train_t.dat"))
run(pipeline(`cat als/data/ratings_test.dat`, `awk -F"::" '{printf "%d |u %d |i %d\n", $3, $1, $2}'`, "als/data/ratings_test_t.dat"))
run(pipeline(`cat als/data/ratings_train_t.dat`, `awk '{print $3}'`, `uniq`, `awk '{printf "|u %d\n", $1}'`, "als/data/users_t_train.dat"))
run(pipeline(`cat als/data/ratings_test_t.dat`, `awk '{print $3}'`, `uniq`, `awk '{printf "|u %d\n", $1}'`, "als/data/users_t_test.dat"))
train_ratings_file = open("als/data/ratings_train.dat", "r")
test_ratings_file = open("als/data/ratings_test.dat", "r")

train_users = []
train_ratings = Dict()
while !eof(train_ratings_file)
  line = readline(train_ratings_file)
  user_id, movie_id, rating, timestamp = split(line, "::")
  if !haskey(train_ratings, user_id)
    train_ratings[user_id] = Dict()
    push!(train_users, user_id)
  end
  train_ratings[user_id][movie_id] = rating
end

test_users = []
test_ratings = Dict()
while !eof(test_ratings_file)
  line = readline(test_ratings_file)
  user_id, movie_id, rating, timestamp = split(line, "::")
  if !haskey(test_ratings, user_id)
    test_ratings[user_id] = Dict()
    push!(test_users, user_id)
  end
  test_ratings[user_id][movie_id] = rating
end

open(`vw --passes 10 -q ui --rank 10 --l2 0.01 --learning_rate 0.015 --decay_learning_rate 0.97 --power_t 0 -f als/data/movielens.reg --cache_file als/data/movielens.cache`, "w", STDOUT) do io
  for user_id in train_users
    for (movie_id, rating) in train_ratings[user_id]
      println(io, "$rating |u $user_id |i $movie_id")
    end
  end
end

actuals = []
open(`vw -i als/data/movielens.reg -t -p als/data/movielens_preds.txt`, "w", STDOUT) do io
  for user_id in test_users
    for (movie_id, rating) in test_ratings[user_id]
      push!(actuals, rating)
      println(io, "|u $user_id |i $movie_id")
    end
  end
end

preds = split(readstring(open("als/data/movielens_preds.txt", "r")), "\n")
pos = 1
rmses = []
for pred in preds
  if pred != ""
    pred = parse(Float64, pred)
    actual = parse(Float64, actuals[pos])
    push!(rmses, (actual - pred) ^ 2)
    pos += 1
  end
end
rmse = sqrt(sum(rmses) / length(rmses))
rm("als/data/movies_t.dat")
rm("als/data/ratings_s.dat")
rm("als/data/ratings_test.dat")
rm("als/data/ratings_test_t.dat")
rm("als/data/ratings_train.dat")
rm("als/data/ratings_train_t.dat")
rm("als/data/users_t_test.dat")
rm("als/data/users_t_train.dat")
rm("als/data/movielens.cache")
rm("als/data/movielens.reg")
rm("als/data/movielens_preds.txt")
testfile = open("test_results.txt", "a")
write(testfile, "\nALS in JuliaVW\n")
current_time = now()
write(testfile, "$current_time\n")
write(testfile, "RMSE: $rmse\n")
println("RMSE: $rmse")
time = now() - then
write(testfile, "Time: $time\n")
println("Time: $time")
speed = Float64(time) / num_lines * 1000
write(testfile, "Speed: $speed mcs/row\n")
println("Speed: $speed mcs/row")
