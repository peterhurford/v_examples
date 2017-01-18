from vowpal_platypus import run, logistic_regression
import argparse
import os
from datetime import datetime

start = datetime.now()
print('...Starting at ' + str(start))

print("Setting up...")
start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--cores')
cores = int(parser.parse_args().cores)

model = logistic_regression(name='Criteo', debug=True, debug_rate=500000, cores=cores)

def process_line(item, predict=False):
    # Split tab separated file
    items = item.replace('\n', '').split('\t')
    if not predict:
        label = items.pop(0)
    interval_items = {}
    categorical_items = []
    for pos, item in enumerate(items):
        if item and item != '':
            if pos < 13:
                interval_items['i' + str(pos)] = int(item)
            else:
                categorical_items.append('c' + str(pos) + str(item))
    items = {
        'i': interval_items,
        'c': categorical_items
    }
    if not predict:
        items['label'] = -1 if int(label) == 0 else 1
    return items

def process_predict_line(item):
    return process_line(item, predict=True)

results = run(model,
              train_filename='criteo/data/train.txt',
              train_line_function=process_line,
              predict_filename='criteo/data/test.txt',
              predict_line_function=process_predict_line,
              header=False)
transformed_preds = map(lambda p: (p + 1) / 2.0, map(lambda p: float(str(p).replace('\n', '')), results))
end = datetime.now()
print('Num Predicted: ' + str(len(transformed_preds)))
print('Elapsted model time: ' + str(end - start))
print('Model speed: ' + str((end - start).total_seconds() * 1000000 / float(len(transformed_preds))) + ' mcs/row')

ids = range(60000000, 66042135)
submission = zip(ids, transformed_preds)
submission_file = open('criteo/data/kaggle_criteo_submission.txt', 'w')
submission_file.write('Id,Predicted\n')
for line in submission:
    submission_file.write(str(line[0]) + ',' + str(line[1]) + '\n')
submission_file.flush()
writing_done = datetime.now()
print('Elapsted file write time: ' + str(writing_done - end))
