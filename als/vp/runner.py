from vowpal_platypus import run, als, logistic_regression, safe_remove, load_file, split_file
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

vw_models = als(name='ALS',
                passes=40,
                quadratic='cp',
                l1=0.001,
                l2=0.001,
                learning_rate=0.015,
                decay_learning_rate=0.97,
                power_t=0,
                rank=10,
                cores=cores)

def compile_ratings(ratings_filename):
    ratings = {}
    ratings_file = open(ratings_filename, 'r')
    while True:
        item = ratings_file.readline()
        if not item:
            break
        item = item.split('::')
        rating = item[2]
        user_id = item[0]
        movie_id = item[1]
        if ratings.get(user_id) is None:
            ratings[user_id] = {} 
        ratings[user_id][movie_id] = rating
    return ratings

def vw_process_line(audiences, customer_id, product_id):
    return {
        'label': actions[customer_id][product_id]['has_ctr'],
        'c': customer_id,
        'p': product_id
    }
    
filename = 'als/data/ratings.dat'
num_lines = sum(1 for line in open(filename))
train = int(ceil(num_lines * 0.8))
test = int(floor(num_lines * 0.2))
os.system('head -n {} als/data/ratings.dat > als/data/ratings_train.dat'.format(train))
os.system('tail -n {} als/data/ratings.dat > als/data/ratings_test.dat'.format(test))
split_file('als/data/ratings_train.dat', cores)
split_file('als/data/ratings_test.dat', cores)
def run_core(model):
    core = 0 if model.node is None else model.node
    filename = 'als/data/ratings_train.dat' + (str(core) if core >= 10 else '0' + str(core))
    ratings = compile_ratings(filename)
    with model.training():
        for (user, rating_data) in ratings.iteritems():
            for (movie, rating) in rating_data.iteritems():
                model.push_instance({'label': rating, 'c': user, 'p': movie})
    filename = 'als/data/ratings_test.dat' + (str(core) if core >= 10 else '0' + str(core))
    ratings = compile_ratings(filename)
    with model.predicting():
        actuals = []
        for (user, rating_data) in ratings.iteritems():
            for (movie, rating) in rating_data.iteritems():
                actuals.append(rating)
                model.push_instance({'c': user, 'p': movie})
    return zip(model.read_predictions(), actuals)

all_results = sum(run(vw_models, run_core), [])

def rmse(results):
    return (sum(map(lambda x: (float(x[1]) - float(x[0])) ** 2, results)) / float(len(results))) ** 0.5

print("Cleaning up...")
safe_remove('ALS*')
safe_remove('als/data/ratings_test*')
safe_remove('als/data/ratings_train*')

rmse = 'RMSE: ' + str(rmse(all_results))
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
