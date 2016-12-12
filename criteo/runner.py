from vowpal_porpoise import run, logistic_regression, safe_remove, load_file, split_file
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
targets = ['Criteo*', 'train.txt0*', 'test.txt0*', 'train2.*', 'train3.*', 'test2*']
[safe_remove(target) for target in targets]

print("Setting up...")
start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--cores')
parser.add_argument('--model')
cores = int(parser.parse_args().cores)
model = parser.parse_args().model

vw_models = logistic_regression(name='Criteo',
                                passes=80,
                                l1=0.00000001,
                                l2=0.00000001,
                                cores=cores,
                                debug_rate=100000)
os.system('head -n 1000000 train.txt > train2.txt')
os.system('tail -n 100000 train2.txt > test2.txt')
os.system('tail -n 1100000 train2.txt > train3.txt')
split_file('train3.txt', cores)
split_file('test2.txt', cores)


def vw_process_line(item, predict=False):
    # Split tab separated file
    item = item.split('\t')
    if not predict:
        label = item.pop(0)
    
    interval_items = filter(lambda x: x.isdigit(), item[1:])
    # Identify empty interval items
    interval_items = map(lambda x: None if x == '' else int(x), interval_items)
    # Set name and values for interval items
    interval_items = dict(zip(map(lambda x: 'i' + x, map(str, range(len(interval_items)))), interval_items))
    # Handle empty interval items
    interval_items = dict([(k, v) for (k, v) in interval_items.iteritems() if v])

    categorical_items = filter(lambda x: not x.isdigit(), item[1:])
    # Handle empty categorical values
    categorical_items = filter(lambda x: x != '', categorical_items)
    items = {
        'i': interval_items,
        'c': categorical_items
    }
    if not predict:
        items['label'] = -1 if int(label) == 0 else 1
    return items

if model == 'logistic':
    def run_core(model):
        core = 0 if model.node is None else model.node
        filename = 'train3.txt' + (str(core) if core >= 10 else '0' + str(core))
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
                        print '{}: done {}%'.format(filename, done)
                        curr_done = done
                    model.push_instance(vw_process_line(item))
        filename = 'test2.txt' + (str(core) if core >= 10 else '0' + str(core))
        num_lines = sum(1 for line in open(filename))
        actuals = []
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
                        print '{}: done {}%'.format(filename, done)
                        curr_done = done
                    item = vw_process_line(item)
                    actuals.append(item['label'])
                    model.push_instance(item)
        return zip(model.read_predictions(), actuals)
else:
    if model == 'random':
        get_pred = lambda: -1 if randint(0, 1) == 0 else 1
    elif model == 'no':
        get_pred = lambda: -1
    elif model == 'yes':
        get_pred = lambda: 1

    def run_core(model):
        core = 0 if model.node is None else model.node
        filename = 'train3.txt' + (str(core) if core >= 10 else '0' + str(core))
        num_lines = sum(1 for line in open(filename))
        actuals = []
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
                    print '{}: done {}%'.format(filename, done)
                    curr_done = done
                item = vw_process_line(item)
                actuals.append([get_pred(), item['label']])
        return actuals

all_results = sum(run(vw_models, run_core), [])

no_results = filter(lambda x: x[1] == -1, all_results)
yes_results = filter(lambda x: x[1] == 1, all_results)


def log_loss(results):
     predicted = [min([max([x, 1e-15]), 1-1e-15]) for x in map(lambda x: float(x[0]), results)]
     target = [min([max([x, 1e-15]), 1-1e-15]) for x in map(lambda x: float(x[1]), results)]
     return -(1.0 / len(target)) * sum([target[i] * log(predicted[i]) + (1.0 - target[i]) * log(1.0 - predicted[i]) for i in xrange(len(target))])

def rmse(results):
    return (sum(map(lambda x: (x[1] - x[0]) ** 2, results)) / len(results)) ** 0.5

def percent_correct(results):
    mean_pred = max(sum(map(lambda x: x[0], results)) / len(results), -0.99999)
    return sum(map(lambda x: x[1] == (-1 if x[0] < mean_pred else 1), results)) / float(len(results)) * 100

mean_pred = max(sum(map(lambda x: x[0], all_results)) / len(all_results), -0.99999)
true_positives = sum(map(lambda x: x[0] >= mean_pred, filter(lambda x: x[1] == 1, all_results)))
true_negatives = sum(map(lambda x: x[0] < mean_pred, filter(lambda x: x[1] == -1, all_results)))
false_positives = sum(map(lambda x: x[0] >= mean_pred, filter(lambda x: x[1] == -1, all_results)))
false_negatives = sum(map(lambda x: x[0] < mean_pred, filter(lambda x: x[1] == 1, all_results)))
precision = true_positives / max(float((true_positives + false_positives)), 1.0)
recall = true_positives / max(float((true_positives + false_negatives)), 1.0)

print('Num Predicted: ' + str(len(all_results)))
print('Num Actual No: ' + str(len(no_results)))
print('Num Predicted No: ' + str(false_negatives + true_negatives))
print('Num Actual Yes: ' + str(len(yes_results)))
print('Num Predicted Yes: ' + str(false_positives + true_positives))
print('Mean Pred: ' + str(mean_pred))
print('Actual Yes/Yes + No: ' + str((true_positives + false_negatives) / float(false_positives + true_positives + false_negatives + true_negatives) * 100) + '%')
print('Predicted Yes/Yes + No: ' + str((false_positives + true_positives) / float(false_positives + true_positives + false_negatives + true_negatives) * 100) + '%')
print('Overall RMSE: ' + str(rmse(all_results)))
print('No RMSE: ' + str(rmse(no_results)))
print('Yes RMSE: ' + str(rmse(yes_results)))
print('Overall LL: ' + str(log_loss(all_results)))
print('No LL: ' + str(log_loss(no_results)))
print('Yes LL: ' + str(log_loss(yes_results)))
print('Overall % correct: ' + str(percent_correct(all_results)) + '%')
print('No % correct: ' + str(percent_correct(no_results)) + '%')
print('Yes % correct: ' + str(percent_correct(yes_results)) + '%')
print('True Positives: ' + str(true_positives))
print('True Negatives: ' + str(true_negatives))
print('False Positives: ' + str(false_positives))
print('False Negatives: ' + str(false_negatives))
print('FP + 100FN / N: ' + str((false_positives + 100 * false_negatives) / float(len(all_results))))
print('Precision: ' + str(precision * 100) + '%')
print('Recall: ' + str(recall * 100) + '%')
print('F: ' + str(2 * ((precision * recall) / max(precision + recall, 0.000001))))
print('MCC: ' + str(((true_positives * true_negatives) - (false_positives * false_negatives)) / sqrt(float(max((true_positives + false_positives) * (true_positives + false_negatives) * (true_negatives + false_positives) * (true_negatives + false_negatives), 1.0)))))
print('AAcc: ' + str(0.5 * ((true_positives / float(true_positives + false_negatives)) + (true_negatives / float(true_negatives + false_positives)))))

end = datetime.now()
print('Elapsted time: ' + str(end - start))
print('Speed: ' + str((end - start).total_seconds() * 1000 / float(len(all_results))) + ' ms/row')
import pdb
pdb.set_trace()
