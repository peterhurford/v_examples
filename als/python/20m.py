#!/usr/bin/env python

from vowpal_porpoise import VW
from datetime import datetime
import os

start = datetime.now()
vw = VW(moniker='ALS', passes=10, quadratic='ui', rank=10, l2=0.001, learning_rate=0.015, decay_learning_rate=0.97, power_t=0)
ratings = open('ratings.csv', 'r')
movie_file = open('movies.csv', 'r')
os.system("tail -n +2 ratings.csv | awk -F\",\" '{print $1}' | uniq > users.dat")
user_file = open('users.dat', 'r')
movie_ids = [movie.split(',')[0] for movie in list(movie_file.read().splitlines())]
user_ids = [user.split(',')[0] for user in list(user_file.read().splitlines())]
movie_file.close()
user_file.close()
rec_file = open('py_recs.dat', 'w')
setup_done = datetime.now()

print "Jamming some train..."
with vw.training():
    line = ratings.readline()  # Throw out header
    for r in xrange(20000263):  # Read in ratings
        line = ratings.readline()
        item = line.split(',')
        vw_item = item[2] + ' |u ' + item[0]  + ' |i ' + item[1]
        vw.push_instance(vw_item)
training_done = datetime.now()

print "Spooling predictions..."
with vw.predicting():
    for user_id in user_ids:
        vw_user = '|u ' + user_id
        for movie_id in movie_ids:
            vw_movie = '|i ' + movie_id
            vw_item = vw_user + ' ' + vw_movie
            vw.push_instance(vw_item)
predicting_done = datetime.now()

print "Generating recs..."
predictions = list(vw.read_predictions_()) # TODO: This will have to be read line by line.
for u, user_id in enumerate(user_ids):
    user_recs = []
    user_preds = predictions[u * 27278 : (u + 1) * 27278]
    if u % 100 == 0:
        print u
    for m, pred in enumerate(user_preds):
        user_recs.append([pred, movie_ids[m]])
    user_recs.sort(reverse=True)
    rec_file.write(str({'user': user_id,
                        'products': map(lambda x: x[1], user_recs[:10])}) + '\n')
rec_file.close()
ratings.close()
recs_done = datetime.now()
print "Timing..."
print "Set up in " + str(setup_done - start)
print "Training in " + str(training_done - setup_done)
print "Predicting in " + str(predicting_done - training_done)
print "Reccing in " + str(recs_done - predicting_done)
print "Total: " + str(recs_done - start)

# TOTAL: ?

# TODO: Filter out the already rated
# TODO: Multithread predict