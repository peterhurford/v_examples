## Using VP to predict Criteo ad clicks

Using data from the [Criteo Kaggle Challenge](https://www.kaggle.com/c/criteo-display-ad-challenge), train on 45.8M rows of user ad clicks (or no clicks) and then test on 6M rows to generate predictions.

Gets a log loss of 0.67848 in 16min1sec of training and 6sec of file writing on a c4.8xlarge (36 core 60GB RAM), which is enough to get position #612 on the leaderboard. This does not beat the logistic regression benchmark, so more tuning and optimization will be needed.
