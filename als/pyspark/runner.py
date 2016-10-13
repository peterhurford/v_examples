# Example usage: rm -r recs; spark-submit --master local[*] --driver-memory 6G --num-executors 9 --executor-memory 5G --executor-cores 3 --packages com.databricks:spark-csv_2.11:1.5.0 runner.py --partisions 81 --num_ratings 20000000

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
parser.add_argument('--num_ratings')
parser.add_argument('--evaluate')
parser.add_argument('--evaluate_only')
partitions = int(parser.parse_args().partitions)
num_ratings = int(parser.parse_args().num_ratings)
evaluate = parser.parse_args().evaluate is not None
evaluate_only = parser.parse_args().evaluate_only is not None
if evaluate_only:
    evaluate = True

sc = SparkContext(appName="VWProtoTestSpark")
sc.setLogLevel("ERROR")
sql_context = SQLContext(sc)

print("Setting up, formatting for {} partitions...".format(partitions))
sql_context.setConf("spark.sql.shuffle.partitions", str(partitions))

ratings = (sql_context.read
           .format('com.databricks.spark.csv')
           .option('header', 'true')
           .option('inferSchema', 'true')
           .load('ratings.csv')
           .select('userId', 'movieId', 'rating'))
ratings = ratings.limit(num_ratings).repartition(partitions).cache()
movies = (sql_context.read
          .format('com.databricks.spark.csv')
          .option('header', 'true')
          .option('inferSchema', 'true')
          .load('movies.csv')
          .select('movieId'))
movies = movies.repartition(partitions).cache()
users = ratings.select('userId').distinct()
users = users.repartition(partitions).cache()
print(str(users.count()) + " users, " + str(ratings.count()) + " ratings, " + str(movies.count()) + " movies.")

print("Have faith...")
model = ALS(rank=20, maxIter=20, userCol='userId', itemCol='movieId', ratingCol='rating')
if not evaluate_only:
# Create a matrix of all product-user combinations.
    predict_data = (ratings.select('userId').drop_duplicates(['userId'])
                    .join(ratings.select('movieId').drop_duplicates(['movieId']))
                    .select('userId', 'movieId'))
    predict_data = (predict_data.join(ratings, ['userId', 'movieId'], how='left_outer')
                    .where(col('rating').isNull())
                    .drop('rating'))
    preds = (model.fit(ratings)
            .transform(predict_data))
    preds = (preds
            .rdd
            .map(lambda x: (x.userId, [[x.prediction, x.movieId]]))
            .reduceByKey(lambda x, y: x + y)
            .mapValues(lambda x: sorted(x, reverse=True)[:10])
            .saveAsTextFile("recs"))

if evaluate:
    train, test = ratings.randomSplit([0.8, 0.2])
    evaluate = model.fit(train).transform(test)
    evaluate.show()
    se = (evaluate.withColumn('sqerror', (col('prediction') - col('rating')) ** 2)
          .select('sqerror')
          .map(lambda x: x.sqerror)
          .collect())
    se = filter(lambda x: x > 0, se)
    n = float(evaluate.count())
    rmse = (sum(se)/n) ** 0.5
    print("Root-mean-square error = " + str(rmse))

done = datetime.now()
print("Timing: " + str(done - start))

# Total: 13m32s (1M), ? (2M), 26m1s (5M), ? (10M), ? (20M)
# Root-mean-square error for 1M = 0.817792985504
# ...on c3.4xlarge (30G RAM 16 core)
