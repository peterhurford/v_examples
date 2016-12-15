from vowpal_platypus import logistic_regression, run
from sklearn import metrics
import re
import numpy

def clean(s):
  return " ".join(re.findall(r'\w+', s,flags = re.UNICODE | re.LOCALE)).lower()

def auc(results):
    preds = map(lambda x: -1 if x < 0.0 else 1, map(lambda x: x[0], results))
    actuals = map(lambda x: x[1], results)
    return metrics.roc_auc_score(numpy.array(preds), numpy.array(actuals))

# VW trains on a file line by line. We need to define a function to turn each CSV line
# into an output that VW can understand.
def process_line(item):
    item = item.split(',')  # CSV is comma separated, so we unseparate it.
    features = [            # A set of features for VW to operate on.
                 'passenger_class_' + clean(item[2]),  # VP accepts individual strings as features.
                 'last_name_' + clean(item[3]),
                 {'gender': 0 if item[5] == 'male' else 1},  # Or VP can take a dict with a number.
                 {'siblings_onboard': int(item[7])},
                 {'family_members_onboard': int(item[8])},
                 {'fare': float(item[10])},
                 'embarked_' + clean(item[12])
               ]
    title = item[4].split(' ')
    if len(title):
        features.append('title_' + title[1])  # Add a title feature if they have one.
    age = item[6]
    if age.isdigit():
        features.append({'age': int(item[6])})
    return {    # VW needs to process a dict with a label and then any number of feature sets.
        'label': 1 if item[1] == '1' else -1,
        'f': features   # The name 'f' for our feature set is arbitrary, but is the same as the 'ff' above that creates quadratic features.
    }

# Train a logistic regression model on Titanic survival.
# The `run` function will automatically generate a train - test split.
run(logistic_regression(name='Titanic', # Gives a name to the model file.
                        passes=40,      # How many online passes to do.
                        quadratic='ff', # Generates automatic quadratic features.
                        l1=0,           # L1 and L2 Regularization
                        l2=0.01),
    'titanic/data/titanic.csv',         # File with the data
    line_function=process_line,         # Function to process each line of the file
    evaluate_function=auc)              # Function to evaluate results
