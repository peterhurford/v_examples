#!/usr/bin/env python

# Example usage: python runner.py --train_cores 40 --predict_cores 20 --num_ratings 20000000

from vowpal_porpoise import VW
from datetime import datetime
from multiprocessing import Pool
import os
import argparse
import random
import socket
from retrying import retry

print "Setting up..."
start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--volume')
parser.add_argument('--op_sys')
parser.add_argument('--train_cores')
parser.add_argument('--predict_cores')
parser.add_argument('--num_ratings')
parser.add_argument('--evaluate')
parser.add_argument('--evaluate_only', action='store_true', default=False)
volume = parser.parse_args().volume
op_sys = parser.parse_args().op_sys
if volume is None:
    volume = os.getcwd()
volume = volume + '/'
if op_sys is None:
    op_sys = 'ubuntu'
train_cores = int(parser.parse_args().train_cores)
predict_cores = int(parser.parse_args().predict_cores)
num_ratings = int(parser.parse_args().num_ratings)
evaluate = parser.parse_args().evaluate
evaluate_only = parser.parse_args().evaluate_only
if evaluate_only and (evaluate is None or evaluate is False):
    evaluate = "ib"

print "Cleaning up..."
targets = ['ALS*', 'ratings_*', '*recs*', 'users.csv']
[os.system('rm ' + volume + target) for target in targets]

print "Booting models..."
def vw_model(node):
    return VW(moniker='{}ALS'.format(volume), total=train_cores, node=node, unique_id=0, span_server='localhost', holdout_off=True, bits=21, passes=40, quadratic='ui', rank=25, l2=0.001, learning_rate=0.015, decay_learning_rate=0.97, power_t=0)
vw_instances = [vw_model(n) for n in range(train_cores)]

print "Formating data..."
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

def train_on_core(core):
    vw = vw_instances[core]
    user_id_pool = filter(lambda x: int(x) % train_cores == core, user_ids)
    vw.start_training()
    for user_id in user_id_pool:
        for movie_id, rating in ratings[user_id].iteritems():
            vw_item = rating + ' |u ' + user_id + ' |i ' + movie_id
            vw.push_instance(vw_item)
    vw.close_process()

@retry
def netcat(hostname, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, port))
    s.sendall(content)
    s.shutdown(socket.SHUT_WR)
    data = []
    while True:
        datum = s.recv(1024)
        if datum == '':
            break
        datum = datum.split('\n')
        for dat in datum:
            if dat != '':
                dat = float(dat)
                if 5 >= dat >= 0:
                    data.append(dat)
    s.close()
    return data

os.system("spanning_tree")
if not evaluate_only:
    pool = Pool(cores)
    print "Jamming some train on {} cores...".format(train_cores)
    pool.map(train_on_core, range(train_cores))
    training_done = datetime.now()

    print "Spooling predictions on {} cores...".format(predict_cores)
    train_model = vw_instances[0].get_model_file()
    initial_moniker = vw_instances[0].handle
    
    def daemon(core):
        port = core + 4040
        train_model = vw_instances[core % train_cores].get_model_file()
        initial_moniker = vw_instances[core % train_cores].handle
        return VW(moniker=initial_moniker, daemon=True, old_model=train_model, holdout_off=True, quiet=True, port=port, num_children=2).start_predicting()
    daemons = [daemon(core) for core in random.sample(range(predict_cores), predict_cores)]

    rec_files = [open('/vol/py_recs' + str(i) + '.dat', 'w') for i in range(predict_cores)]
    def rec_for_user(core):
        rfile = rec_files[core]
        port = 4040 + core
        user_id_pool = filter(lambda x: int(x) % predict_cores == core, user_ids)
        for user_id in user_id_pool:
            vw_items = ''
            user_recs = []
            for movie_id in movie_ids:
                if ratings[user_id].get(movie_id) is None:
                    vw_items += '|u ' + user_id + ' |i ' + movie_id + '\n'
            print 'Connecting to port %i...' % port
            preds = netcat('localhost', port, vw_items)
            pos = 0
            for movie_id in movie_ids:
                if ratings[user_id].get(movie_id) is None:
                    user_recs.append([float(preds[pos]), movie_id])
                    pos += 1
            user_recs.sort(reverse=True)
            rfile.write(str({'user': user_id,
                            'products': map(lambda x: x[1], user_recs[:10])}) + '\n')
        rfile.flush()

    pool = Pool(predict_cores)
    pool.map(rec_for_user, range(predict_cores))
    for f in rec_files:
        f.close()
    os.system('cat py_recs* > all_py_recs.csv')

if evaluate:
    print 'Evaluating...'
    if evaluate == 'ib':
        print 'Shuffling for ib evaluate...'
        if op_sys == 'mac':
            shuf = 'gshuf'
            split = 'gsplit'
        else:
            shuf = 'shuf'
            split = 'split'
        os.system("{} ratings_.csv > ratings__.csv; mv ratings__.csv ratings_.csv".format(shuf))
    os.system("{} -d -l {} ratings_.csv".format(split, int(num_ratings * 0.9)))
    os.system("mv x00 ratings_train.csv; mv x01 ratings_test.csv")
    ratings_file = open('ratings_train.csv', 'r')
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
    pool = Pool(train_cores)
    pool.map(train_on_core, range(train_cores))

    ratings = {}
    ratings_file = open('ratings_test.csv', 'r')
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
    
    def daemon(core):
        port = core + 4040
        train_model = vw_instances[core % train_cores].get_model_file()
        initial_moniker = vw_instances[core % train_cores].handle
        return VW(moniker=initial_moniker, daemon=True, old_model=train_model, holdout_off=True, quiet=True, port=port, num_children=2).start_predicting()
    daemons = [daemon(core) for core in random.sample(range(predict_cores), predict_cores)]

    def evaluate_on_core(core):
        port = 4040 + core
        user_id_pool = filter(lambda x: int(x) % predict_cores == core, user_ids)
        all_preds = []
        for user_id in user_id_pool:
            vw_items = ''
            user_ratings = []
            if ratings.get(user_id) is not None:
                for movie_id, rating in ratings[user_id].iteritems():
                    vw_items += '|u ' + user_id + ' |i ' + movie_id + '\n'
                    user_ratings.append(float(rating))
                print 'Connecting to port %i...' % port
                preds = netcat('localhost', port, vw_items)
                all_preds.append(zip(preds, user_ratings))
        all_preds = sum(all_preds, [])
        return sum(map(lambda x: (float(x[0]) - float(x[1])) ** 2, all_preds)) / len(all_preds)
    pool = Pool(predict_cores)
    rmses = pool.map(evaluate_on_core, range(predict_cores))
    rmse = (sum(rmses) / predict_cores) ** 0.5
    print("RMSE: " + str(rmse))
    evaluate_done = datetime.now()

print "Spinning down server..."
os.system("killall spanning_tree")
for port in range(4040, 4040 + predict_cores):
    print "Spinning down port %i" % port
    os.system("pkill -9 -f 'vw.*--port %i'" % port)
recs_done = datetime.now()

print "Timing..."
print "Set up in " + str(setup_done - start)
if not evaluate_only:
    print "Training in " + str(training_done - setup_done)
    print "Reccing in " + str(recs_done - training_done)
    if evaluate:
        print "Evaluating in: " + str(evaluate_done - recs_done)
        print "Total (without evaluate): " + str(recs_done - start)
        print "Total: " + str(evaluate_done - start)
    else:
        print "Total: " + str(recs_done - start)
else:
    print "Evaluating in: " + str(evaluate_done - setup_done)
    print "Total: " + str(evaluate_done - start)

#1M
# Set up in 0:00:01.337433
# Training in 0:00:26.205371
# Reccing in 0:01:17.388643
# Total: 0:01:44.931447

#2M
# Set up in 0:00:02.629749
# Training in 0:00:32.358522
# Reccing in 0:02:40.497983
# Total: 0:03:15.486254

#5M
# Set up in 0:00:06.840877
# Training in 0:00:44.052366
# Reccing in 0:06:34.695909
# Total: 0:07:25.589152

#10M
# Set up in 0:00:13.321389
# Training in 0:01:06.611161
# Reccing in 0:14:10.492325
# Total: 0:15:30.424875

#20M
# Set up in 0:00:27.044442
# Training in 0:01:46.621141
# Reccing in 0:33:12.592734
# Total: 0:35:26.258317

# ...on m4.16xlarge (64 core 256GB)
