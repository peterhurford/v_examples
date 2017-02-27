## Pyspark example with Titanic Kaggle data.
## Run with `spark-submit --master local[4] --driver-memory 8G --packages com.databricks:spark-csv_2.11:1.5.0 titanic/spark/example.py --partitions 16`.

from datetime import datetime
start = datetime.now()

from pyspark import SparkContext
from pyspark.sql import SQLContext, HiveContext
from pyspark.sql.functions import udf, col
from pyspark.ml.feature import VectorAssembler, OneHotEncoder, StringIndexer
from pyspark.sql.types import DoubleType
from pyspark.ml.classification import LogisticRegression

from vowpal_platypus.evaluation import auc

import argparse


parser = argparse.ArgumentParser()
parser.add_argument('--partitions')
partitions = int(parser.parse_args().partitions)

sc = SparkContext(appName='PySparkTitanicTest')
sc.setLogLevel('ERROR')
sql_context = SQLContext(sc)
sql_context.setConf('spark.sql.shuffle.partitions', str(partitions))

titanic = (sql_context.read
           .format('com.databricks.spark.csv')
           .options(header='true', inferschema='true')
           .load('titanic/data/titanic.csv')
           .repartition(partitions))

def title(name):
    title = name.split('.')[0].split(',')[1].strip()
    if title in ['Capt', 'Don', 'Major', 'Dona', 'Lady', 'the Countess', 'Jonkheer']:
        return 'Sir'
    else:
        return title
title_udf = udf(title)

titanic = (titanic.withColumn('Title', title_udf('Name')).drop('Name')
           .na.drop()
           .drop('PassengerId').drop('Ticket').drop('Cabin'))

si = StringIndexer(inputCol='Sex', outputCol='sex')
indexed_df = si.fit(titanic).transform(titanic).drop('Sex')
si = StringIndexer(inputCol='Embarked', outputCol='embarked_dummy')
indexed_df = si.fit(indexed_df).transform(indexed_df).drop('Embarked')
si = StringIndexer(inputCol='Title', outputCol='title_dummy')
indexed_df = si.fit(indexed_df).transform(indexed_df).drop('Title')
hot = OneHotEncoder(inputCol='embarked_dummy', outputCol='embarked_vector')
hot_df = hot.transform(indexed_df).drop('embarked_dummy')
hot = OneHotEncoder(inputCol='title_dummy', outputCol='title_vector')
hot_df = hot.transform(hot_df).drop('title_dummy')
vect = VectorAssembler(inputCols=list(set(hot_df.columns) - set(['Survived'])), outputCol='features')
vect_df = vect.transform(hot_df)

train, test = vect_df.randomSplit([0.8, 0.2])
test_labels = test.select('Survived')

train = (train.select(col('Survived').cast(DoubleType()), 'features')
         .withColumnRenamed('Survived', 'label'))
test = test.select('features')

lr = LogisticRegression(maxIter=10, regParam=0.3)
preds = [p[0] for p in lr.fit(train).transform(test).select('prediction').collect()]
actuals = [a[0] for a in test_labels.collect()]
auc = 'AUC: ' + str(auc(zip(preds, actuals)))
end = datetime.now()
time = 'Time: ' + str((end - start).total_seconds()) + ' sec'
num_lines = sum(1 for line in open('titanic/data/titanic.csv', 'r'))
speed = 'Speed: ' + str((end - start).total_seconds() * 1000000 / float(num_lines)) + ' mcs/row'
with open('test_results.txt', 'a') as test_file:
    for line in ['\n', 'TITANIC IN PYSPARK\n', str(datetime.now()) + '\n', auc + '\n', time + '\n', speed + '\n']:
        test_file.write(line)
print(auc)
print(time)
print(speed)
