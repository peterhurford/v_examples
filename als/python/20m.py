#!/usr/bin/env python

from vowpal_porpoise import VW
from datetime import datetime
from copy import copy
from multiprocessing import Pool
import os

start = datetime.now()
vw = VW(moniker='ALS', passes=5, quadratic='ui', rank=10, l2=0.001, learning_rate=0.015, decay_learning_rate=0.97, power_t=0)

print "Setting up..."
ratings_file = open('ratings.csv', 'r')
ratings_file.readline() # Throw out header
movie_file = open('movies.csv', 'r')
os.system("tail -n +2 ratings.csv | awk -F\",\" '{print $1}' | uniq > users.csv")
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


print "Jamming some train..."
with vw.training():
    for user_id, user_ratings in ratings.iteritems():
        for movie_id, rating in user_ratings.iteritems():
            vw_item = rating + ' |u ' + user_id + ' i ' + movie_id
            vw.push_instance(vw_item)
training_done = datetime.now()

print "Spooling predictions..."
cores = 16
vw_test = [copy(vw) for _ in range(cores)]
for vw_instance in vw_test:
    vw_instance.start_predicting()
for u, user_id in enumerate(user_ids):
    for movie_id in movie_ids:
        if ratings[user_id].get(movie_id) is None:
            vw_item = "'" + user_id + "x" + movie_id + " |u " + user_id + "|i " + movie_id
            vw_test[u % cores].push_instance(vw_item)
for vw_instance in vw_test:
    vw_instance.close_process()
predicting_done = datetime.now()

print "Generating recs..."
prediction_files = [open(vw_instance.prediction_file, 'r') for vw_instance in vw_test]
rec_files = [open('py_recs' + str(i) + '.dat', 'w') for i in range(cores)]

def write_recs(user_id, user_recs, rec_file):
    user_recs.sort(reverse=True)
    rec_file.write(str({'user': user_id,
                        'products': map(lambda x: x[1], user_recs[:10])}) + '\n')

def rec_for_user(pool):
    pfile = prediction_files[pool]
    rfile = rec_files[pool]
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
print "Timing..."
print "Set up in " + str(setup_done - start)
print "Training in " + str(training_done - setup_done)
print "Predicting in " + str(predicting_done - training_done)
print "Reccing in " + str(recs_done - predicting_done)
print "Total: " + str(recs_done - start)

# Set up in 0:00:30.890973
# Training in 0:02:03.457164
# Predicting in 5:13:08.389028
# Reccing in 0:24:46.010530
# Total: 5:40:28.747695
# ...on c3.4xlarge (30G RAM 16 core)
