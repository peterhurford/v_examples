## Libraries
import numpy
import os
import pandas
import random
from sklearn import datasets

## Import
titanic = pandas.read_csv("../data/titanic.csv")

## Impute NAs with Median
def impute(col):
  if col.apply(numpy.isreal).all(axis = 0):
    value = numpy.nanmedian(col)
  else:
    value = col.mode().iloc[0]
  return col.fillna(value)

for col in titanic.columns[titanic.isnull().any(axis = 0)]:
  titanic[col] = impute(titanic[col])

def split_to_title(x):
  return x.split(".")[0].split(",")[1].strip()

titanic["Title"] = titanic["Name"].apply(split_to_title)
titanic["Title"].replace("Mme", "Mlle", inplace = True)
for title in ["Capt", "Don", "Major"]:
  titanic["Title"].replace(title, "Sir", inplace = True)
for title in ["Dona", "Lady", "the Countess", "Jonkheer"]:
  titanic["Title"].replace(title, "Sir", inplace = True)

#### Clean Data for XGB
dep_var = titanic["Survived"]
titanic.drop(["PassengerId", "Survived", "Name", "Ticket", "Cabin"], axis = 1, inplace = True)

#### Dummyize Data for XGB
factor_vars = titanic.columns[titanic.applymap(lambda x: type(x) == str).any()]
for factor_var in factor_vars:
  dummy_vars = pandas.get_dummies(titanic[factor_var])
  titanic = pandas.concat([titanic.drop(factor_var, axis = 1), dummy_vars], axis = 1)

##### Separate Into Train, Validation, and Test for XGB
TEST_PCT = 0.2
is_train_data = [random.random() > TEST_PCT for x in range(len(titanic))]
titanic_train = titanic[is_train_data]
titanic_test = titanic[[not x for x in is_train_data]]
dep_var_train = dep_var[is_train_data]
dep_var_test = dep_var[[not x for x in is_train_data]]

VALIDATION_PCT = 0.1
is_validation_data = [random.random() > VALIDATION_PCT for x in range(len(titanic_train))]
titanic_validation = titanic_train[is_validation_data]
titanic_train = titanic_train[[not x for x in is_validation_data]]
dep_var_validation = dep_var_train[is_validation_data]
dep_var_train = dep_var_train[[not x for x in is_validation_data]]

#### Write libsvm files
f = open('train.txt', 'w')
datasets.dump_svmlight_file(titanic_train, dep_var_train, f)
f.close()
f = open('validation.txt', 'w')
datasets.dump_svmlight_file(titanic_validation, dep_var_validation, f)
f.close()
f = open('test.txt', 'w')
datasets.dump_svmlight_file(titanic_test, dep_var_test, f)
f.close()
