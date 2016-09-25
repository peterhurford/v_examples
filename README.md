# Prototype of Implementing Vowpal Wabbit for Machine Learning Systems

* **[ALS](als)** -- Run [Alternating Least Squares Collaborative Filtering](https://github.com/JohnLangford/vowpal_wabbit/wiki/Matrix-factorization-example) on different amounts of [MovieLens data](http://grouplens.org/datasets/movielens/). Capable of analyzing 20M product ratings and create recommendations for 3,777,893,888 user-product combinations in 1h53m2s on 4x c3.4xlarge machines (combined 64 cores with 120GB RAM).

* [Random](random)** -- Pair customers with random recommendations from a product list. Generates seven billion random recommendations in 12m39s on 4x c3.4xlarge machines (combined 64 cores with 120GB RAM).
