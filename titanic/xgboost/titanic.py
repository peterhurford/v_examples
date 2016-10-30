import xgboost

### Train XGB from libsvm file.
### See https://xgboost.readthedocs.io/en/latest/how_to/external_memory.html
def train_out_of_memory():
  titanic_train = xgboost.DMatrix('train.txt#dtrain.cache')
  titanic_validation = xgboost.DMatrix('validation.txt#dvalidation.cache')
  watchlist = [(titanic_train, "train"), (titanic_validation, "eval")]
  params = {"eta": 1, "max_depth": 2, "nthread": 2, "objective": "binary:logistic"}
  return xgboost.train(params, titanic_train, 2000, watchlist)
model = train_out_of_memory()

def predict_out_of_memory(model):
  titanic_test = xgboost.DMatrix('test.txt#dtest.cache')
  preds = model.predict(titanic_test)
  return metrics.roc_auc_score(numpy.array(dep_var_test), preds)
print predict_out_of_memory(model)

# TODO: ValueError: feature_names mismatch
