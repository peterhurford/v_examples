## Import Titanic data from spreadsheet, impute NAs with median, create title feature, separate into train and test, fit an XGB to the data, get test AUC.

## Libraries
from datetime import datetime
start = datetime.now()
import numpy
import os
import pandas
import xgboost
import random
from sklearn import metrics, datasets

## Import
titanic = pandas.read_csv("../data/titanic.csv")


## Impute NAs with Median
print titanic.isnull().apply(sum)
# PassengerId      0
# Survived         0
# Pclass           0
# Name             0
# Sex              0
# Age            177
# SibSp            0
# Parch            0
# Ticket           0
# Fare             0
# Cabin          687
# Embarked         2

def impute(col):
  if col.apply(numpy.isreal).all(axis = 0):
    value = numpy.nanmedian(col)
  else:
    value = col.mode().iloc[0]
  return col.fillna(value)


for col in titanic.columns[titanic.isnull().any(axis = 0)]:
  titanic[col] = impute(titanic[col])

print titanic.isnull().apply(sum)
# PassengerId    0
# Survived       0
# Pclass         0
# Name           0
# Sex            0
# Age            0
# SibSp          0
# Parch          0
# Ticket         0
# Fare           0
# Cabin          0
# Embarked       0


def split_to_title(x):
  return x.split(".")[0].split(",")[1].strip()

titanic["Title"] = titanic["Name"].apply(split_to_title)
titanic["Title"].replace("Mme", "Mlle", inplace = True)
for title in ["Capt", "Don", "Major"]:
  titanic["Title"].replace(title, "Sir", inplace = True)
for title in ["Dona", "Lady", "the Countess", "Jonkheer"]:
  titanic["Title"].replace(title, "Sir", inplace = True)

titanic["Title"].value_counts()
# Mr        517
# Miss      182
# Mrs       125
# Master     40
# Sir         8
# Dr          7
# Rev         6
# Mlle        3
# Col         2
# Ms          1


## Fit XGB

#### Clean Data for XGB
dep_var = titanic["Survived"]
titanic.drop(["PassengerId", "Survived", "Name", "Ticket", "Cabin"], axis = 1, inplace = True)

#### Dummyize Data for XGB
factor_vars = titanic.columns[titanic.applymap(lambda x: type(x) == str).any()]
for factor_var in factor_vars:
  dummy_vars = pandas.get_dummies(titanic[factor_var])
  titanic = pandas.concat([titanic.drop(factor_var, axis = 1), dummy_vars], axis = 1)

##### Separate Into Train, Validation, and Test for XGB
TEST_PCT = 0.1
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

#### Turn data into matrix for XGB
params = {"eta": 1, "max_depth": 2, "nthread": 2, "objective": "binary:logistic"}

def train(titanic_train, titanic_validation, titanic_test, params):
  titanic_train = xgboost.DMatrix(titanic_train, label = dep_var_train)
  titanic_validation = xgboost.DMatrix(titanic_validation, label = dep_var_validation)
  titanic_test = xgboost.DMatrix(titanic_test, label = dep_var_test)

  watchlist = [(titanic_train, "train"), (titanic_validation, "eval")]
  return xgboost.train(params, titanic_train, 400, watchlist)
model = train(titanic_train, titanic_validation, titanic_test, params)

## Get Test AUC
def predict(titanic_test, dep_var_test):
  titanic_test = xgboost.DMatrix(titanic_test, label = dep_var_test)
  preds = model.predict(titanic_test)
  return metrics.roc_auc_score(numpy.array(dep_var_test), preds)
print "AUC: " + str(predict(titanic_test, dep_var_test))
print "Time: " + str(datetime.now() - start)

# AUC: 0.76245210728
# Time: 0:00:00.646733
