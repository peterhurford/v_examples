## Import Titanic data from spreadsheet, impute NAs with median, create title feature, separate into train and test, fit an XGB to the data, get test AUC.

## Libraries
from datetime import datetime
start = datetime.now()
from vowpal_platypus import logistic_regression, safe_remove, run
from sklearn import metrics
from math import ceil, floor
import re
import os
import numpy
import argparse

# Setup
parser = argparse.ArgumentParser()
parser.add_argument('--hypersearch', action='store_true', default=False)
hypersearch = parser.parse_args().hypersearch

if hypersearch:
    vw_model = logistic_regression(name='Titanic', passes=[1, 50],
                                   quadratic='ff',
                                   l1=[0.00000001, 0.001], l2=[0.00000001, 0.01])
else:
    vw_model = logistic_regression(name='Titanic', passes=2,
                                   quadratic='ff',
                                   l1=0.0001, l2=0.01)

def clean(s):
  return " ".join(re.findall(r'\w+', s,flags = re.UNICODE | re.LOCALE)).lower()

def process_line(item):
    item = item.split(',')
    features = [
                 'passenger_class_' + clean(item[2]),
                 'last_name_' + clean(item[3]),
                 {'gender': 0 if item[5] == 'male' else 1},
                 {'siblings_onboard': int(item[7])},
                 {'family_members_onboard': int(item[8])},
                 {'fare': float(item[10])},
                 'embarked_' + clean(item[12])
               ]
    title = item[4].split(' ')
    if len(title):
        features.append('title_' + title[1])
    age = item[6]
    if age.isdigit():
        features.append({'age': int(item[6])})
    return {
        'label': 1 if item[1] == '1' else -1,
        'f': features
    }

def auc(results):
    preds = map(lambda x: -1 if x < 0.0 else 1, map(lambda x: x[0], results))
    actuals = map(lambda x: x[1], results)
    return metrics.roc_auc_score(numpy.array(preds), numpy.array(actuals))

all_results = run(vw_model,
                  'titanic/data/titanic.csv',
                  line_function=process_line,
                  evaluate_function=auc)
safe_remove('Titanic.*')

auc = 'AUC: ' + str(auc(all_results))
end = datetime.now()
time = 'Time: ' + str((end - start).total_seconds()) + ' sec'
num_lines = sum(1 for line in open('titanic/data/titanic.csv', 'r'))
speed = 'Speed: ' + str((end - start).total_seconds() * 1000000 / float(num_lines)) + ' mcs/row'
title = 'TITANIC IN PYTHON VP (HYPERSEARCH)' if hypersearch else 'TITANIC IN PYTHON VP'
with open('test_results.txt', 'a') as test_file:
    for line in ['\n', title + '\n', str(datetime.now()) + '\n', auc + '\n', time + '\n', speed + '\n']:
        test_file.write(line)
print(auc)
print(time)
print(speed)

# AUC: 0.845297029703
# Time: 0:00:00.520540
