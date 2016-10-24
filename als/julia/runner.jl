# Example usage: julia runner.py
#TODO: This code is very slow...

#TODO: Up limit to 1M, 20M
run(pipeline(`head -n 10001 ratings.csv`, `tail -n +2`, "ratings_.csv"))
ratings_file = open("ratings_.csv", "r")

run(pipeline(`tail -n +2 ratings_.csv`, `awk -F\",\" '{print $1}'`, `uniq`, "users.csv"))
@everywhere movie_ids = readcsv("movies.csv")[2:end,1]
@everywhere user_ids = readcsv("users.csv")[2:end,1]

ratings = Dict()
while !eof(ratings_file)
  line = readline(ratings_file)
  user_id, movie_id, rating = split(line, ",")
  if !haskey(ratings, user_id)
    ratings[user_id] = Dict()
  end
  ratings[user_id][movie_id] = rating
end
@eval @everywhere ratings = $ratings

run(`spanning_tree`)

@everywhere function train(node)
  user_id_pool = map(x -> string(convert(Int, x)), filter(x -> x % 4 == node, user_ids))
  #TODO: Up passes to 80
  open(`vw --total 4 --node $node --unique_id 0 --span_server localhost --holdout_off --passes 10 -q ui --rank 20 --l2 0.01 --learning_rate 0.015 --decay_learning_rate 0.97 --power_t 0 -f movielens$node.reg --cache_file movielens$node.cache`, "w", STDOUT) do io
    for user_id in user_id_pool
      for (movie_id, rating) in ratings[user_id]
        println(io, "$rating |u $user_id |i $movie_id")
      end
    end
  end
end

@everywhere function predict(node)
  port = 4040 + node
  rec_file = open("jl_recs_$node.txt", "w")
  run(`vw -i movielens0.reg --daemon --holdout_off --port $port --num_children 2`)
  user_id_pool = map(x -> string(convert(Int, x)), filter(x -> x % 4 == node, user_ids))
  for user_id in user_id_pool
    vw_items = ""
    for movie_id in movie_ids
      if !haskey(ratings[user_id], movie_id)
        vw_items *= "|u $user_id |i $movie_id\n"
      end
    end
    vw_items *= "eof"
    println("Connecting to port $port")
    vw_daemon = connect(port)
    println(vw_daemon, vw_items)
    preds = []
    line = readline(vw_daemon)
    while !contains(line, "eof")
      push!(preds, parse(Float64, line))
      line = readline(vw_daemon)
    end
    close(vw_daemon)
    pos = 1
    user_recs = []
    for movie_id in movie_ids
      if !haskey(ratings[user_id], movie_id)
        push!(user_recs, [preds[pos], movie_id])
        pos += 1
      end
    end
    sort!(user_recs, rev = true, by = x -> x[1])
    write(rec_file, string(Dict("user"=>user_id, "products"=>map(x -> x[2], user_recs[1:10]))))
  end
end

t0 = @spawn train(0)
t1 = @spawn train(1)
t2 = @spawn train(2)
t3 = @spawn train(3)
wait(t0)
wait(t1)
wait(t2)
wait(t3)
p0 = @spawn predict(0)
p1 = @spawn predict(1)
p2 = @spawn predict(2)
p3 = @spawn predict(3)
wait(p0)
wait(p1)
wait(p2)
wait(p3)
run(`cat jl_recs*` |> "all_jl_recs.dat")
run(`killall spanning_tree`)
run(`killall vw`)
