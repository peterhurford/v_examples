# Prototype of Implementing Vowpal Wabbit for Machine Learning Systems

* **[ALS](als)** -- Run [Alternating Least Squares Collaborative Filtering](https://github.com/JohnLangford/vowpal_wabbit/wiki/Matrix-factorization-example) on different amounts of [MovieLens data](http://grouplens.org/datasets/movielens/). Capable of analyzing 20M product ratings and create recommendations based on 3,757,811,791 unrated user-product combinations in 35m26s on a m4.10xlarge (40 core, 196GB RAM).

* **[Random](random)** -- Pair customers with random recommendations from a product list. Generates 7,000,000,000 random recommendations in 12m39s on 4x c3.4xlarge machines (combined 120G RAM, 64 cores).

* **[Titanic](titanic)** -- VW in Bash achieves an AUC of 0.8464 in 0.22s. XGBoost in Python achieves an AUC of 0.8106 in 0.67s. These results could easily change with better tuning, but demonstrate that VW is competitive with XGBoost out of the box. Running XGBoost (out of core) and R are work in progress.
