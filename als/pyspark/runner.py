import logging
import argparse
from datetime import datetime

from pyspark import SparkContext
from pyspark.sql import SQLContext, HiveContext
from pyspark.sql.functions import col, asc, desc, lit, monotonically_increasing_id
from pyspark.ml.recommendation import ALS

start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--cores')
parser.add_argument('--rating_count')
cores = int(parser.parse_args().cores)
rating_count = int(parser.parse_args().rating_count)
sc = SparkContext(appName="VWProtoTestSpark")
sql_context = SQLContext(sc)

logging.info("Setting up...")
sql_context.setConf("spark.sql.shuffle.partitions", str(cores * 3))

ratings = (sql_context.read
           .format('com.databricks.spark.csv')
           .option('header', 'true')
           .option('inferSchema', 'true')
           .load('ratings.csv')
           .select('userId', 'movieId', 'rating'))
ratings = ratings.limit(rating_count).repartition(cores * 3).cache()
movies = (sql_context.read
          .format('com.databricks.spark.csv')
          .option('header', 'true')
          .option('inferSchema', 'true')
          .load('movies.csv')
          .select('movieId'))
movies = movies.repartition(cores * 3).cache()
users = ratings.select('userId').distinct()
users = users.repartition(cores * 3).cache()

# Create a matrix of all product-user combinations.
predict_data = (ratings.select('userId').drop_duplicates(['userId'])
                .join(ratings.select('movieId').drop_duplicates(['movieId']))
                .select('userId', 'movieId'))
predict_data = (predict_data.join(ratings, ['userId', 'movieId'], how='left_outer')
                .where(col('rating').isNull())
                .drop('rating'))
model = ALS(rank=10, maxIter=5, userCol='userId', itemCol='movieId', ratingCol='rating')
preds = (model.fit(ratings)
        .transform(predict_data))
preds = (preds
        .rdd
        .map(lambda x: (x.userId, [[x.prediction, x.movieId]]))
        .reduceByKey(lambda x, y: x + y)
        .mapValues(lambda x: sorted(x, reverse=True)[:10])
        .mapValues(lambda xs: map(lambda x: x[1], xs))
        .repartition(200)
        .saveAsTextFile("recs"))
done = datetime.now()
print("Timing: " + str(done - start))

# Total: 13m32s (1M), ? (2M), 26m1s (5M), ? (10M), ? (20M)
# ...on c3.4xlarge (30G RAM 16 core)
