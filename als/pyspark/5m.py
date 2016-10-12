import logging
from datetime import datetime

from pyspark import SparkContext
from pyspark.sql import SQLContext, HiveContext
from pyspark.sql.functions import col, asc, desc, lit, monotonically_increasing_id
from pyspark.ml.recommendation import ALS

start = datetime.now()
sc = SparkContext(appName="VWProtoTestSpark5M")
sql_context = SQLContext(sc)

logging.info("Setting up...")
sql_context.setConf("spark.sql.shuffle.partitions", "12")

ratings = (sql_context.read
           .format('com.databricks.spark.csv')
           .option('header', 'true')
           .option('inferSchema', 'true')
           .load('ratings.csv')
           .select('userId', 'movieId', 'rating'))
ratings = ratings.limit(5000000).repartition(12).cache()  # Limit to 5M for testing.
movies = (sql_context.read
          .format('com.databricks.spark.csv')
          .option('header', 'true')
          .option('inferSchema', 'true')
          .load('movies.csv')
          .select('movieId'))
movies = movies.repartition(12).cache()
users = ratings.select('userId').distinct()
users = users.repartition(12).cache()

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
preds.cache()
print(preds.count())
print(preds.columns)
print(preds.rdd.map(lambda x: (x.userId, [x.prediction, x.movieId])).take(3))
print(preds.rdd.map(lambda x: (x.userId, [x.prediction, x.movieId])).reduceByKey(lambda x, y: x + y).take(3))
done = datetime.now()
print("Timing: " + str(done - start))
import pdb
pdb.set_trace()
        # .rdd
        # .map(lambda x: (x.userId, [x.prediction, x.movieId]))
        # .reduceByKey(lambda x, y: x + y)
        # .mapValues(sorted)
        # .mapValues(lambda x: x[:10]))
# print(preds.take(3))
# 00:23:26
        # .mapValues(lambda xs: map(lambda x: x[2], xs))
        # .saveAsTextFile("recs.txt"))

# Total: ?
# ...on c3.4xlarge (30G RAM 16 core)
