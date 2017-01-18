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

model = logistic_regression(name='Criteo',
                            passes=40,
                            l1=0.000001,
                            l2=0.000001,
                            debug=True,
                            cores=cores)

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

results = run(model,
              train_filename='criteo/train.txt',
              train_line_function=lambda i: vw_process_line(i),
              predict_filename='criteo/test.txt',
              predict_line_function=lambda i: vw_process_line(i, predict=True))
transformed_preds = map(lambda p: (p + 1) / 2.0, map(lambda p: float(p.replace('\n', '')), results))
end = datetime.now()
print('Num Predicted: ' + str(len(transformed_preds)))
print('Elapsted model time: ' + str(end - start))
print('Model speed: ' + str((end - start).total_seconds() * 1000000 / float(len(transformed_preds))) + ' mcs/row')

ids = range(60000000, 66042135)
submission = zip(ids, transformed_preds)
submission_file = open('kaggle_criteo_submission.txt', 'w')
submission_file.write('Id,Predicted\n')
for line in submission:
    submission_file.write(str(line[0]) + ',' + str(line[1]) + '\n')
os.system('zip kaggle_criteo_submission.zip kaggle_criteo_submission.txt')
writing_done = datetime.now()
print('Elapsted file write time: ' + str(writing_done - end))
