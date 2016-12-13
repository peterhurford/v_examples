from vowpal_platypus import run, logistic_regression, safe_remove, load_file, split_file
import argparse
import re
import os
import json
from random import randint
from datetime import datetime
from math import log, sqrt

start = datetime.now()
print('...Starting at ' + str(start))

print("Cleaning up...")
os.system("rm Criteo*")

print("Setting up...")
start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--cores')
cores = int(parser.parse_args().cores)

vw_models = logistic_regression(name='Criteo',
                                passes=40,
                                l1=0.000001,
                                l2=0.000001,
                                cores=cores)
split_file('train.txt', cores)
split_file('test.txt', cores)


def vw_process_line(item, predict=False):
    # Split tab separated file
    item = item.replace('\n', '')
    item = item.split('\t')
    if not predict:
        label = item.pop(0)
    interval_items = filter(lambda x: x.isdigit(), item)
    # Identify empty interval items
    interval_items = map(lambda x: None if x == '' else int(x), interval_items)
    # Set name and values for interval items
    interval_items = dict(zip(map(lambda x: 'i' + x, map(str, range(len(interval_items)))), interval_items))
    # Handle empty interval items
    interval_items = dict([(k, v) for (k, v) in interval_items.iteritems() if v])

    categorical_items = filter(lambda x: not x.isdigit(), item)
    # Handle empty categorical values
    categorical_items = filter(lambda x: x != '', categorical_items)
    items = {
        'i': interval_items,
        'c': categorical_items
    }
    if not predict:
        items['label'] = -1 if int(label) == 0 else 1
    return items

def run_core(model):
    core = 0 if model.node is None else model.node
    filename = 'train.txt' + (str(core) if core >= 10 else '0' + str(core))
    num_lines = sum(1 for line in open(filename))
    with model.training():
        with open(filename, 'r') as filehandle:
            i = 0
            curr_done = 0
            while True:
                item = filehandle.readline()
                if not item:
                    break
                i += 1
                done = int(i / float(num_lines) * 100)
                if done - curr_done > 1:
                    print '{}: training done {}%'.format(filename, done)
                    curr_done = done
                model.push_instance(vw_process_line(item))
    filename = 'test.txt' + (str(core) if core >= 10 else '0' + str(core))
    num_lines = sum(1 for line in open(filename))
    with model.predicting():
        with open(filename, 'r') as filehandle:
            i = 0
            curr_done = 0
            while True:
                item = filehandle.readline()
                if not item:
                    break
                i += 1
                done = int(i / float(num_lines) * 100)
                if done - curr_done > 1:
                    print '{}: predicting done {}%'.format(filename, done)
                    curr_done = done
                model.push_instance(vw_process_line(item, predict=True))
    return None

run(vw_models, run_core)
os.system('cat Criteo*prediction* > all_predictions.dat')
pred_file = open('all_predictions.dat', 'r')
preds = pred_file.readlines()
transformed_preds = map(lambda p: (p + 1) / 2.0, map(lambda p: float(p.replace('\n', '')), preds))
end = datetime.now()
print('Num Predicted: ' + str(len(preds)))
print('Elapsted model time: ' + str(end - start))
print('Model speed: ' + str((end - start).total_seconds() * 1000000 / float(len(preds))) + ' mcs/row')

ids = range(60000000, 66042135)
submission = zip(ids, transformed_preds)
submission_file = open('kaggle_criteo_submission.txt', 'w')
submission_file.write('Id,Predicted\n')
for line in submission:
    submission_file.write(str(line[0]) + ',' + str(line[1]) + '\n')
os.system('zip kaggle_criteo_submission.zip kaggle_criteo_submission.txt')
writing_done = datetime.now()

print('Elapsted file write time: ' + str(writing_done - end))
