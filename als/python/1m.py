#!/usr/bin/env python

from vowpal_porpoise import VW
from datetime import datetime
from copy import copy
from multiprocessing import Pool
import os

start = datetime.now()
vw = VW(moniker='ALS', passes=5, quadratic='ui', rank=10, l2=0.001, learning_rate=0.015, decay_learning_rate=0.97, power_t=0)

ratings = open('ratings.dat', 'r')
movie_file = open('movies.dat', 'r')
user_file = open('users.dat', 'r')
movie_ids = [int(movie.split('::')[0]) for movie in list(movie_file.read().splitlines())]
user_ids = [int(user.split('::')[0]) for user in list(user_file.read().splitlines())]
movie_file.close()
user_file.close()
setup_done = datetime.now()

print "Jamming some train..."
with vw.training():
    for r in xrange(1000209):  # Read in ratings
        line = ratings.readline()
        item = line.split('::')
        vw_item = item[2] + ' |u ' + item[0]  + ' |i ' + item[1]
        vw.push_instance(vw_item)
training_done = datetime.now()

print "Spooling predictions..."
cores = 8
vw_test = [copy(vw) for _ in range(cores)]
for vw_instance in vw_test:
    vw_instance.start_predicting()
for u, user_id in enumerate(user_ids):
    vw_user = '|u ' + str(user_id)
    for movie_id in movie_ids:
        vw_movie = '|i ' + str(movie_id)
        vw_item = vw_user + ' ' + vw_movie
        vw_test[u % cores].push_instance(vw_item)
for vw_instance in vw_test:
    vw_instance.close_process()
predicting_done = datetime.now()

print "Generating recs..."
prediction_files = [open(vw_instance.prediction_file, 'r') for vw_instance in vw_test]
user_id_pools = [filter(lambda x: x % cores == i, user_ids) for i in range(cores)]
rec_files = [open('py_recs' + str(i) + '.dat', 'w') for i in range(cores)]

def rec_for_user(pool):
    user_ids = user_id_pools[pool]
    pfile = prediction_files[pool]
    rfile = rec_files[pool]
    for user_id in user_ids:
        user_recs = []
        for movie_id in movie_ids:
            pred = float(pfile.readline())
            user_recs.append([pred, movie_id])
        user_recs.sort(reverse=True)
        rfile.write(str({'user': user_id,
                         'products': map(lambda x: x[1], user_recs[:10])}) + '\n')
    rfile.flush()

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

# Set up in 0:00:00.011392
# Training in 0:01:07.877544
# Predicting in 0:01:15.753880
# Reccing in 0:00:08.083421
# Total: 0:02:31.726237
# ...on my laptop (16G RAM 8 core Macbook Pro Mid-2015).

# TODO: Filter out the already rated
