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
parser.add_argument('--cores')
parser.add_argument('--num_ratings')
parser.add_argument('--evaluate')
parser.add_argument('--evaluate_only')
cores = int(parser.parse_args().cores)
num_ratings = int(parser.parse_args().num_ratings)
evaluate = parser.parse_args().evaluate is not None
evaluate_only = parser.parse_args().evaluate_only is not None
if evaluate_only:
    evaluate = True

sc = SparkContext(appName="VWProtoTestSpark")
sc.setLogLevel("ERROR")
sql_context = SQLContext(sc)

logging.info("Setting up...")
sql_context.setConf("spark.sql.shuffle.partitions", str(cores * 3))

ratings = (sql_context.read
           .format('com.databricks.spark.csv')
           .option('header', 'true')
           .option('inferSchema', 'true')
           .load('ratings.csv')
           .select('userId', 'movieId', 'rating'))
ratings = ratings.limit(num_ratings).repartition(cores * 3).cache()
movies = (sql_context.read
          .format('com.databricks.spark.csv')
          .option('header', 'true')
          .option('inferSchema', 'true')
          .load('movies.csv')
          .select('movieId'))
movies = movies.repartition(cores * 3).cache()
users = ratings.select('userId').distinct()
users = users.repartition(cores * 3).cache()

model = ALS(rank=40, maxIter=40, userCol='userId', itemCol='movieId', ratingCol='rating')
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
            .mapValues(lambda xs: map(lambda x: x[1], xs))
            .saveAsTextFile("recs"))

if evaluate:
    train, test = ratings.randomSplit([0.8, 0.2])
    evaluate = model.fit(train).transform(test)
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
