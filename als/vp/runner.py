from vowpal_platypus import run, als, safe_remove
import argparse
import re
import os
import json
from random import randint
from datetime import datetime
from math import log, ceil, floor

start = datetime.now()
print('...Starting at ' + str(start))

print("Setting up...")
start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--cores')
parser.add_argument('--num_ratings')
cores = int(parser.parse_args().cores)
num_ratings = parser.parse_args().num_ratings
if num_ratings is None:
    num_ratings = 1000000
else:
    num_ratings = int(num_ratings)

def compile_rating(item):
    item = item.split('::')
    rating = item[2]
    user_id = item[0]
    movie_id = item[1]
    return {'label': rating, 'c': user_id, 'p': movie_id}

def rmse(results):
    return (sum(map(lambda x: (float(x[1]) - float(x[0])) ** 2, results)) / float(len(results))) ** 0.5

if num_ratings < 1000000:
    os.system('head -n ' + str(num_ratings) + ' als/data/ratings.dat > als/data/ratings_.dat')
else:
    os.system('cp als/data/ratings.dat als/data/ratings_.dat')

results = run(als(name='ALS', passes=10, cores=cores,
                  quadratic='cp', rank=10,
                  l2=0.01, learning_rate=0.015, decay_learning_rate=0.97, power_t=0),
              'als/data/ratings_.dat',
              line_function=compile_rating,
              header=False)

rmse = 'RMSE: ' + str(rmse(results))
end = datetime.now()
time = 'Time: ' + str((end - start).total_seconds()) + ' sec'
speed = 'Speed: ' + str((end - start).total_seconds() * 1000000 / float(num_ratings)) + ' mcs/row'
with open('test_results.txt', 'a') as test_file:
    for line in ['\n', 'MOVIELENS IN VP\n', str(datetime.now()) + '\n', rmse + '\n', time + '\n', speed + '\n']:
        test_file.write(line)
print(rmse)
print(time)
print(speed)
