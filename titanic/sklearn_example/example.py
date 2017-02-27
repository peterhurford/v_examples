from datetime import datetime
start = datetime.now()
from sklearn.linear_model import LogisticRegression
from sklearn import metrics
import pandas
import numpy
import random

titanic = pandas.read_csv('titanic/data/titanic.csv')


# Add title data
def split_to_title(x):
  return x.split('.')[0].split(',')[1].strip()

titanic['Title'] = titanic['Name'].apply(split_to_title)
titanic['Title'].replace('Mme', 'Mlle', inplace = True)
for title in ['Capt', 'Don', 'Major']:
  titanic['Title'].replace(title, 'Sir', inplace = True)
for title in ['Dona', 'Lady', 'the Countess', 'Jonkheer']:
  titanic['Title'].replace(title, 'Sir', inplace = True)


## Impute NAs with Median
def impute(col):
  if col.apply(numpy.isreal).all(axis = 0):
    value = numpy.nanmedian(col)
  else:
    value = col.mode().iloc[0]
  return col.fillna(value)

for col in titanic.columns[titanic.isnull().any(axis = 0)]:
  titanic[col] = impute(titanic[col])

# Collect dep_var and drop polluted variables
dep_var = titanic['Survived']
titanic.drop(['PassengerId', 'Survived', 'Name', 'Ticket', 'Cabin'], axis = 1, inplace = True)

## Dummyize
titanic['Sex'] = titanic['Sex'].apply(lambda sex: 1 if sex == 'male' else 0)

factor_vars = titanic.columns[titanic.applymap(lambda x: type(x) == str).any()]
for factor_var in factor_vars:
  dummy_vars = pandas.get_dummies(titanic[factor_var])
  titanic = pandas.concat([titanic.drop(factor_var, axis = 1), dummy_vars], axis = 1)

## Train model
is_train_data = [random.random() < 0.8 for x in range(len(titanic))]
train_dep_var = dep_var[is_train_data].values
titanic_train = titanic[is_train_data]
train_data = titanic_train.values
test_dep_var = dep_var[[not x for x in is_train_data]].values
titanic_test = titanic[[not x for x in is_train_data]]
model = LogisticRegression()
model.fit(train_data, train_dep_var)
predicted = model.predict(titanic_test)

auc = 'AUC: ' + str(metrics.roc_auc_score(test_dep_var, predicted))
end = datetime.now()
time = 'Time: ' + str((end - start).total_seconds()) + ' sec'
num_lines = sum(1 for line in open('titanic/data/titanic.csv', 'r'))
speed = 'Speed: ' + str((end - start).total_seconds() * 1000000 / float(num_lines)) + ' mcs/row'
with open('test_results.txt', 'a') as test_file:
    for line in ['\n', 'TITANIC IN SKLEARN\n', str(datetime.now()) + '\n', auc + '\n', time + '\n', speed + '\n']:
        test_file.write(line)
print(auc)
print(time)
print(speed)
