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
cores = int(parser.parse_args().cores)

def compile_rating(item):
    item = item.split('::')
    rating = item[2]
    user_id = item[0]
    movie_id = item[1]
    return {'label': rating, 'c': user_id, 'p': movie_id}

def rmse(results):
    return (sum(map(lambda x: (float(x[1]) - float(x[0])) ** 2, results)) / float(len(results))) ** 0.5

results = run(als(name='ALS', passes=40, cores=cores,
                  quadratic='cp', rank=10,
                  l1=0.001, l2=0.001,
                  learning_rate=0.015, decay_learning_rate=0.97, power_t=0),
              'als/data/ratings.dat',
              line_function=compile_rating,
              evaluate_function=rmse,
              header=False)

rmse = 'RMSE: ' + str(rmse(results))
end = datetime.now()
time = 'Time: ' + str((end - start).total_seconds()) + ' sec'
num_lines = sum(1 for line in open('als/data/ratings.dat', 'r'))
speed = 'Speed: ' + str((end - start).total_seconds() * 1000000 / float(num_lines)) + ' mcs/row'
with open('test_results.txt', 'a') as test_file:
    for line in ['\n', 'MOVIELENS IN VP\n', str(datetime.now()) + '\n', rmse + '\n', time + '\n', speed + '\n']:
        test_file.write(line)
print(rmse)
print(time)
print(speed)
