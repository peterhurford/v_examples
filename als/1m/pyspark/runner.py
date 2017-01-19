# Example usage: spark-submit --master local[*] --driver-memory 6G --packages com.databricks:spark-csv_2.11:1.5.0 runner.py --partitions 16 --num_ratings 1000

import logging
import argparse
import math
import os
from datetime import datetime

from pyspark import SparkContext
from pyspark.sql import SQLContext, HiveContext
from pyspark.sql.functions import col, asc, desc, lit, monotonically_increasing_id
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--partitions')
parser.add_argument('--num_ratings')
partitions = int(parser.parse_args().partitions)
num_ratings = parser.parse_args().num_ratings
if num_ratings is None:
    num_ratings = 1000000
else:
    num_ratings = int(num_ratings)

sc = SparkContext(appName='PySparkALSTest')
sc.setLogLevel('ERROR')
sql_context = SQLContext(sc)

print('Setting up, formatting for {} process partitions...'.format(partitions))
sql_context.setConf('spark.sql.shuffle.partitions', str(partitions))

if num_ratings < 1000000:
    os.system('head -n ' + str(num_ratings) + ' als/1m/data/ratings.dat > als/1m/data/ratings_.dat')
else:
    os.system('cp als/1m/data/ratings.dat als/1m/data/ratings_.dat')

ratings = (sc.textFile('file://' + os.getcwd() + '/als/1m/data/ratings_.dat')
           .repartition(partitions)
           .flatMap(lambda x: [y.split('::') for y in x.split('\n')])
           .toDF()
           .select(col('_1').alias('user_id'), col('_2').alias('movie_id'), col('_3').alias('rating')))

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

os.system('rm als/1m/data/ratings_.dat')

done = datetime.now()
time = "Time: " + str((done - start).total_seconds()) + ' sec'
print(time)
speed = "Speed: " + str((done - start).total_seconds() * 1000000 / float(num_ratings)) + ' mcs per row'
print(speed)
with open('test_results.txt', 'a') as test_file:
    for line in ['\n', 'MOVIELENS IN PYSPARK\n', str(datetime.now()) + '\n', rmse + '\n', time + '\n', speed + '\n']:
        test_file.write(line)
