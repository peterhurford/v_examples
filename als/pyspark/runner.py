# Example usage: spark-submit --master local[*] --driver-memory 6G --packages com.databricks:spark-csv_2.11:1.5.0 runner.py --partitions 16

import logging
import argparse
import math
from datetime import datetime

from pyspark import SparkContext
from pyspark.sql import SQLContext, HiveContext
from pyspark.sql.functions import col, asc, desc, lit, monotonically_increasing_id
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--partitions')
partitions = int(parser.parse_args().partitions)

sc = SparkContext(appName="PySparkALSTest")
sc.setLogLevel("ERROR")
sql_context = SQLContext(sc)

print("Setting up, formatting for {} process partitions...".format(partitions))
sql_context.setConf("spark.sql.shuffle.partitions", str(partitions))

ratings = sc.textFile('als/data/ratings.dat').flatMap(lambda x: x.split('::'))
import pdb
pdb.set_trace()

ratings = (sql_context.read
           .format('com.databricks.spark.csv')
           .option('inferSchema', 'true')
           .load('als/data/ratings.dat')
           .select('userId', 'movieId', 'rating'))
ratings = ratings.repartition(partitions)
movies = (sql_context.read
          .format('com.databricks.spark.csv')
          .option('inferSchema', 'true')
          .load('als/data/movies.dat')
          .select('movieId'))
movies = movies.repartition(partitions)
users = ratings.select('userId').distinct()
users = users.repartition(partitions)
ratings = ratings.cache()
movies = movies.cache()
users = users.cache()
print(str(users.count()) + " users, " + str(ratings.count()) + " ratings, " + str(movies.count()) + " movies.")

print("Have faith...")
model = ALS(rank=10, maxIter=10, userCol='userId', itemCol='movieId', ratingCol='rating')
train, test = ratings.randomSplit([0.9, 0.1])
evaluate = model.fit(train).transform(test)
se = (evaluate.withColumn('sqerror', (col('prediction') - col('rating')) ** 2)
      .select('sqerror')
      .map(lambda x: x.sqerror)
      .collect())
se = filter(lambda x: x > 0, se)
n = float(evaluate.count())
rmse = (sum(se)/n) ** 0.5
print("RMSE: " + str(rmse))

done = datetime.now()
print("Time: " + str(done - start))
