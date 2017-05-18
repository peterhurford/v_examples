from vowpal_platypus import run
from vowpal_platypus.models import logistic_regression
from vowpal_platypus.evaluate_function import auc
import argparse
import os
from datetime import datetime
from sklearn import metrics
import numpy

start = datetime.now()
print('...Starting at ' + str(start))

print("Setting up...")
start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--cores')
parser.add_argument('--playground', action='store_true', default=False)
cores = int(parser.parse_args().cores)
playground = parser.parse_args().playground

def compile_item(item, predict=False):
    item = item.replace('false', '0').replace('true', '1')
    items = [i.replace('\n', '').replace('"', '').replace(' ', '').replace(':', '').lower() for i in item.split(',')]
    t_id = items.pop(0)
    if not predict:
        label = items.pop(-1)
    interval_items = filter(lambda x: x.replace('-', '').replace('.', '').isdigit(), items)
    interval_items = dict(zip(map(lambda x: 'i' + x, map(str, range(len(interval_items)))), interval_items))
    categorical_items = filter(lambda x: not x.replace('-', '').replace('.', '').isdigit(), items)
    categorical_items = map(lambda x, y: 'c_' + x + y, map(str, range(len(categorical_items))), categorical_items)
    features = {
        'i': interval_items,
        'c': categorical_items
    }
    if not predict:
        features['label'] = -1 if int(label) == 0 else 1
    return features

model = logistic_regression(name='Springleaf', passes=10, cores=cores, debug=True)
if playground:  # For model tuning and such
    results = run(model,
                  'springleaf/train.csv',
                  line_function=compile_item,
                  evaluate_function=auc)
    import pdb
    pdb.set_trace()

full_results = run(model,
                   train_filename='springleaf/train.csv',
                   train_line_function=lambda i: compile_item(i),
                   predict_filename='springleaf/test.csv',
                   predict_line_function=lambda i: compile_item(i, predict=True))
print("Model trained!")
submission_file = open('springleaf/submission.csv', 'w')
submission_file.write('"ID","target"\n')
test_file = open('springleaf/test.csv')
test_file.readline()
for pred in full_results:
    t_id = str(test_file.readline().split(',')[0])
    submission_file.write(t_id + ',' + str((pred + 1) / 2.0) + '\n')
submission_file.flush()
submission_file.close()
print("Submission file written!")
end = datetime.now()
print('Time: ' + str((end - start).total_seconds()) + ' sec')
