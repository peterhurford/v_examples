## Import Titanic data from spreadsheet, impute NAs with median, create title feature, separate into train and test, fit an XGB to the data, get test AUC.

## Libraries
from datetime import datetime
start = datetime.now()
from vowpal_platypus import linear_regression
from sklearn import metrics
from math import ceil, floor
import re
import os
import numpy

# Setup
vw_model = linear_regression(name='Titanic', passes=40,
                             quadratic='ff',
                             l1=0.0000001, l2=0.0000001)

filename = '../data/titanic.csv'
num_lines = sum(1 for line in open(filename)) - 1
train = int(ceil(num_lines * 0.8))
test = int(floor(num_lines * 0.2))
os.system('head -n {} {} > titanic.dat'.format(num_lines, filename))
os.system('head -n {} titanic.dat > titanic_train.dat'.format(train))
os.system('tail -n {} titanic.dat > titanic_test.dat'.format(test))

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

with vw_model.training():
    with open('titanic_train.dat', 'r') as filehandle:
        filehandle.readline() # Throwaway header
        while True:
            item = filehandle.readline()
            if not item:
                break
            vw_model.push_instance(process_line(item))
with vw_model.predicting():
    actuals = []
    with open('titanic_test.dat', 'r') as filehandle:
        filehandle.readline() # Throwaway header
        while True:
            item = filehandle.readline()
            if not item:
                break
            item = process_line(item)
            actuals.append(item['label'])
            vw_model.push_instance(item)
all_results = zip(vw_model.read_predictions(), actuals)
preds = map(lambda x: x[0], all_results)
actuals = map(lambda x: x[1], all_results)

## TODO: Impute NAs with Median
# def impute(col):
#   if col.apply(numpy.isreal).all(axis = 0):
#     value = numpy.nanmedian(col)
#   else:
#     value = col.mode().iloc[0]
#   return col.fillna(value)

# for col in titanic.columns[titanic.isnull().any(axis = 0)]:
#   titanic[col] = impute(titanic[col])

d_preds = map(lambda x: -1 if x < 0.0 else 1, preds)
print 'ROC: ' + str(metrics.roc_auc_score(numpy.array(d_preds), numpy.array(actuals)))
end = datetime.now()
print 'Time: ' + str(end - start)

# AUC: 0.845297029703
# Time: 0:00:00.520540
