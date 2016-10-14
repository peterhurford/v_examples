#!/usr/bin/env python

# Example usage: python runner.py --cores 36 --num_ratings 20000000

from vowpal_porpoise import VW
from datetime import datetime
from copy import copy
from multiprocessing import Pool
import os
import argparse
import random

print "Setting up..."
start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--cores')
parser.add_argument('--num_ratings')
parser.add_argument('--evaluate')
parser.add_argument('--evaluate_only')
cores = int(parser.parse_args().cores)
num_ratings = int(parser.parse_args().num_ratings)
evaluate = parser.parse_args().evaluate
evaluate_only = parser.parse_args().evaluate_only is not None
if evaluate_only and evaluate is None:
    evaluate = "ib"
vw = VW(moniker='ALS', learning_rate=0.1, l2=0.000001, bits=24, passes=100, quadratic='ui', rank=20, power_t=0.333)

os.system("head -n {} ratings.csv | tail -n +2 > ratings_.csv".format(num_ratings + 1)) # +1 to not trim header
os.system("tail -n +2 ratings_.csv | awk -F\",\" '{print $1}' | uniq > users.csv")

ratings_file = open('ratings_.csv', 'r')
movie_file = open('movies.csv', 'r')
user_file = open('users.csv', 'r')
movie_ids = [movie.split(',')[0] for movie in list(movie_file.read().splitlines())]
user_ids = [user.split(',')[0] for user in list(user_file.read().splitlines())]
movie_ids.pop(0) # Throw out headers
user_ids.pop(0)

ratings = {}
while True:
    item = ratings_file.readline()
    if not item:
        break
    item = item.split(',')
    rating = item[2]
    user_id = item[0]
    movie_id = item[1]
    if ratings.get(user_id) is None:
        ratings[user_id] = {} 
    ratings[user_id][movie_id] = rating

movie_file.close()
user_file.close()
ratings_file.close()
setup_done = datetime.now()

if not evaluate_only:
    print "Jamming some train..."
    with vw.training():
        for user_id, user_ratings in ratings.iteritems():
            for movie_id, rating in user_ratings.iteritems():
                vw_item = rating + ' |u ' + user_id + ' i ' + movie_id
                vw.push_instance(vw_item)
    training_done = datetime.now()

    print "Spooling predictions..."
    vw_test = [copy(vw) for _ in range(cores)]

    def predict_on_core(core):
        vw_instance = vw_test[core]
        user_id_pool = filter(lambda x: int(x) % cores == core, user_ids)
        vw_instance.start_predicting()
        for user_id in user_id_pool:
            for movie_id in movie_ids:
                if ratings[user_id].get(movie_id) is None:
                    vw_item = "'" + user_id + "x" + movie_id + " |u " + user_id + "|i " + movie_id
                    vw_instance.push_instance(vw_item)
        return vw_instance.prediction_file

    pool = Pool(cores)
    prediction_files = pool.map(predict_on_core, range(cores))
# for vw_instance in vw_test:
#     vw_instance.close_process()
    predicting_done = datetime.now()

    print "Generating recs..."
    prediction_files = [open(f) for f in prediction_files] # [vw_instance.prediction_file, 'r') for vw_instance in vw_test]
    rec_files = [open('py_recs' + str(i) + '.dat', 'w') for i in range(cores)]

    def write_recs(user_id, user_recs, rec_file):
        user_recs.sort(reverse=True)
        rec_file.write(str({'user': user_id,
                            'products': map(lambda x: x[1], user_recs[:10])}) + '\n')

    def rec_for_user(core):
        pfile = prediction_files[core]
        rfile = rec_files[core]
        current_user_id = None
        user_recs = []
        while True:
            line = pfile.readline()
            if not line:
                write_recs(current_user_id, user_recs, rfile)
                rfile.flush()
                break
            line = line.split(' ')
            pred = float(line[0])
            data = line[1].split('x')
            user_id = data[0]
            movie_id = int(data[1])
            if current_user_id is None:
                current_user_id = user_id
            if user_id != current_user_id:
                write_recs(current_user_id, user_recs, rfile)
                current_user_id = user_id
                user_recs = []
            user_recs.append([pred, movie_id])
    pool = Pool(cores)
    pool.map(rec_for_user, range(cores))
    for f in prediction_files:
        f.close()
    for f in rec_files:
        f.close()
    os.system("cat py_recs* > all_py_recs.dat")
    recs_done = datetime.now()

if evaluate:
    print "Evaluating..."
    if evaluate == "ib":
        print "Shuffling for ib evaluate..."
        os.system("gshuf ratings_.csv > ratings__.csv; mv ratings__.csv ratings_.csv")
    ratings_file = open('ratings_.csv', 'r')
    vw2 = copy(vw)
    num_train = int(num_ratings * 0.8)
    with vw2.training():
        for i in xrange(num_train):
            item = ratings_file.readline()
            item = item.split(',')
            rating = item[2]
            user_id = item[0]
            movie_id = item[1]
            vw_item = rating + ' |u ' + user_id + ' i ' + movie_id
            vw2.push_instance(vw_item)
    with vw2.predicting():
        for i in xrange(num_ratings - num_train):
            item = ratings_file.readline()
            item = item.split(',')
            rating = item[2]
            user_id = item[0]
            movie_id = item[1]
            vw_item = rating + ' |u ' + user_id + ' i ' + movie_id
            vw2.push_instance(vw_item)
    evaluate_done = datetime.now()

print "Timing..."
print "Set up in " + str(setup_done - start)
if not evaluate_only:
    print "Training in " + str(training_done - setup_done)
    print "Predicting in " + str(predicting_done - training_done)
    print "Reccing in " + str(recs_done - predicting_done)
    if evaluate:
        print "Evaluating in: " + str(evaluate_done - recs_done)
        print "Total: " + str(evaluate_done - start)
    else:
        print "Total: " + str(recs_done - start)
else:
    print "Evaluating in: " + str(evaluate_done - setup_done)
    print "Total: " + str(evaluate_done - start)

# 1M
# Set up in 0:00:01.589956
# Training in 0:00:09.532032
# Predicting in 0:04:28.629261
# Reccing in 0:01:03.216326
# Total: 0:05:42.967575
# IB RMSE = 0.824037
# OOB RMSE = 1.001956

# 2M
# Set up in 0:00:03.504287
# Training in 0:00:26.993131
# Predicting in 0:10:16.670008
# Reccing in 0:02:10.684090
# Total: 0:12:57.851516

# 5M
# Set up in 0:00:07.977441
# Training in 0:00:32.729757
# Predicting in 0:22:29.189496
# Reccing in 0:05:46.371634
# Total: 0:28:56.268328

# 10M
# Set up in 0:00:17.477135
# Training in 0:03:28.911870
# Predicting in 0:46:51.979080
# Reccing in 0:12:00.531361
# Total: 1:02:38.899446

# 20M
# Set up in 0:00:34.069401
# Training in 0:09:17.816559
# Predicting in 1:41:37.228382
# Reccing in 0:24:58.254132
# Total: 2:16:27.368474

# ...on c3.4xlarge (30G RAM 16 core)
