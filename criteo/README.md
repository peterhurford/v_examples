## Using VP to predict Criteo ad clicks

Using data from the [Criteo Kaggle Challenge](https://www.kaggle.com/c/criteo-display-ad-challenge), train on 45.8M rows of user ad clicks (or no clicks) and then test on 6M rows to generate predictions.

Gets a log loss of 0.54649 in 5min30sec of training and 8sec of file writing on a m4.10xlarge (40 core 160GB RAM), which is enough to get position #543 on the leaderboard. This does not beat the logistic regression benchmark (LL = 0.48396, position #415), so more tuning and optimization will be needed.
