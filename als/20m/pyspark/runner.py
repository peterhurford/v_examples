# Example usage: spark-submit --master local[*] --driver-memory 6G --packages com.databricks:spark-csv_2.11:1.5.0 runner.py --partitions 16

import logging
import argparse
import os
from datetime import datetime

from pyspark import SparkContext
from pyspark.sql import SQLContext
from pyspark.sql.functions import col
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--partitions')
partitions = int(parser.parse_args().partitions)

sc = SparkContext(appName='PySparkALSTest')
sc.setLogLevel('ERROR')
sql_context = SQLContext(sc)

print('Setting up, formatting for {} process partitions...'.format(partitions))
sql_context.setConf('spark.sql.shuffle.partitions', str(partitions))

ratings = (sql_context.read.format('com.databricks.spark.csv')
           .options(header='true')
           .options(inferSchema='true')
           .load('file://' + os.getcwd() + '/als/20m/data/ratings.csv')

users = ratings.select('user_id').distinct()
movies = ratings.select('movie_id').distinct()
ratings = ratings.cache()
movies = movies.cache()
users = users.cache()
print(str(users.count()) + " users, " + str(ratings.count()) + " ratings, " + str(movies.count()) + " movies.")

print("Have faith...")
model = ALS(rank=10, maxIter=10, userCol='user_id', itemCol='movie_id', ratingCol='rating')
train, test = ratings.randomSplit([0.8, 0.2])
evaluate = model.fit(train).transform(test)
se = (evaluate.withColumn('sqerror', (col('prediction') - col('rating')) ** 2)
      .select('sqerror')
      .map(lambda x: x.sqerror)
      .collect())
se = filter(lambda x: x > 0, se)
n = float(evaluate.count())
rmse = (sum(se)/n) ** 0.5
rmse = "RMSE: " + str(rmse)
print(rmse)

done = datetime.now()
time = "Time: " + str((done - start).total_seconds()) + ' sec'
print(time)
speed = "Speed: " + str((done - start).total_seconds() * 1000000 / float(num_ratings)) + ' mcs per row'
print(speed)
