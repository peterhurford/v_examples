## Import Titanic data from spreadsheet, impute NAs with median, create title feature, separate into train and test, fit an XGB to the data, get test AUC.

## Libraries
from datetime import datetime
start = datetime.now()
from vowpal_platypus import run
from vowpal_platypus.models import logistic_regression
from vowpal_platypus.evaluation import auc
from vowpal_platypus.utils import clean
import argparse

# Setup
parser = argparse.ArgumentParser()
parser.add_argument('--hypersearch', action='store_true', default=False)
hypersearch = parser.parse_args().hypersearch

if hypersearch:
    vw_model = logistic_regression(name='Titanic', passes=[1, 5],
                                   quadratic='ff',
                                   nn=[5, 10, 15, 20],
                                   l1=[0.00000001, 0.001], l2=[0.00000001, 0.01])
else:
    vw_model = logistic_regression(name='Titanic', passes=3, quadratic='ff', data_file=True)

def process_line(item, predict=False):
    item = item.split(',')
    if not predict:
        label = item.pop(1)
    features = ['passenger_class_' + clean(item[1]),
                 {'gender': 0 if item[4] == 'male' else 1},
                 {'siblings_onboard': int(item[6])},
                 {'family_members_onboard': int(item[7])},
                 'embarked_' + clean(item[11])]
    last_name = clean(item[2]).split(' ')
    if len(last_name):
        features.append('last_' + last_name[0])
    title = clean(item[3]).split(' ')
    if len(title):
        features.append('title_' + title[0])
    try:
        features.append({'age': float(item[5])})
    except:
        pass
    fare = item[9]
    if fare.isdigit():
        features.append({'fare': int(fare)})
    if predict:
        return {'f': features}
    else:
        return {'label': 1 if label == '1' else -1, 'f': features}

evaluate_function = auc if hypersearch else None
all_results = run(vw_model,
                  'titanic/data/titanic.csv',
                  line_function=process_line,
                  evaluate_function=evaluate_function)

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
