#!/usr/bin/env python

# Example usage: python runner.py --cores 36 --num_ratings 20000000

from vowpal_porpoise import VW
from datetime import datetime
from multiprocessing import Pool
import os
import argparse
import random
import socket
from retrying import retry

print "Cleaning up..."
os.system("rm ALS* ratings_* *py_recs* users.csv")
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

def vw_model(node):
    return VW(moniker='ALS', total=cores, node=node, unique_id=0, span_server='localhost', holdout_off=True, passes=80, quadratic='ui', rank=20, l2=0.01, learning_rate=0.015, decay_learning_rate=0.97, power_t=0)
vw_instances = [vw_model(n) for n in range(cores)]

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
    user_id_pool = filter(lambda x: int(x) % cores == core, user_ids)
    vw.start_training()
    for user_id in user_id_pool:
        for movie_id, rating in ratings[user_id].iteritems():
            vw_item = rating + ' |u ' + user_id + ' i ' + movie_id
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
                data.append(dat)
    s.close()
    return data

if not evaluate_only:
    pool = Pool(cores)
    print "Provisioning server for {} cores...".format(cores)
    os.system("spanning_tree")
    print "Jamming some train..."
    pool.map(train_on_core, range(cores))
    training_done = datetime.now()

    print "Spooling predictions..."
    train_model = vw_instances[0].get_model_file()
    initial_moniker = vw_instances[0].handle
    
    def daemon(port):
        return VW(moniker=initial_moniker, daemon=True, old_model=train_model, holdout_off=True, quiet=True, port=port, num_children=2).start_predicting()
    daemons = [daemon(port) for port in range(4040, 4040 + cores)]

    rec_files = [open('py_recs' + str(i) + '.dat', 'w') for i in range(cores)]
    def rec_for_user(core):
        rfile = rec_files[core]
        port = 4040 + core
        user_id_pool = filter(lambda x: int(x) % cores == core, user_ids)
        for user_id in user_id_pool:
            vw_items = ''
            user_recs = []
            for movie_id in movie_ids:
                if ratings[user_id].get(movie_id) is None:
                    vw_items += '|u ' + user_id + '|i ' + movie_id + '\n'
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

    pool = Pool(cores)
    pool.map(rec_for_user, range(cores))
    for f in rec_files:
        f.close()
    os.system("cat py_recs* > all_py_recs.dat")

    print "Spinning down server..."
    os.system("killall spanning_tree")
    for port in range(4040, 4040 + cores):
        print "Spinning down port %i" % port
        os.system("pkill -9 -f 'vw.*--port %i'" % port)
    recs_done = datetime.now()

if evaluate:  #TODO: Update
    print "Evaluating..."
    if evaluate == "ib":
        print "Shuffling for ib evaluate..."
        os.system("gshuf ratings_.csv > ratings__.csv; mv ratings__.csv ratings_.csv")
    os.system("gsplit -d -l {} ratings_.csv".format(int(num_ratings * 0.8)))
    os.system("mv x00 ratings_train.dat; mv x01 ratings_test.dat")
    ratings_file = open('ratings_train.dat', 'r')
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
    pool = Pool(cores)
    pool.map(train_on_core, range(cores))

    def evaluate_on_core(core):
        vw = vw_instances[core]
        user_id_pool = filter(lambda x: int(x) % cores == core, user_ids)
        vw.start_predicting()
        for user_id in user_id_pool:
            for movie_id, rating in ratings[user_id].iteritems():
                vw_item = rating + ' |u ' + user_id + ' i ' + movie_id
                vw.push_instance(vw_item)
        vw.close_process()
    ratings_file = open('ratings_test.dat', 'r')
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
    pool = Pool(cores)
    pool.map(train_on_core, range(cores))
    evaluate_done = datetime.now()

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

#2M

#5M

#10M

#20M

# ...on c3.4xlarge (30G RAM 16 core)
