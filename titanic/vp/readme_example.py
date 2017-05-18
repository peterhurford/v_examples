from vowpal_platypus import run                        # The run function is the main function for running VP models.
from vowpal_platypus.models import logistic_regression # vowpal_platypus.models is where all the models are imported from.
from vowpal_platypus.evaluation import auc             # vowpal_platypus.evaluation can import a lot of evaluation functions, like AUC.
from vowpal_platypus.utils import clean                # vowpal_platypus.utils has some useful utility functions.

# VW trains on a file line by line. We need to define a function to turn each CSV line
# into an output that VW can understand.
def process_line(item):
    item = item.split(',')  # CSV is comma separated, so we unseparate it.
    features = [            # A set of features for VW to operate on.
                 'passenger_class_' + clean(item[2]),  # VP accepts individual strings as features.
                 {'gender': 0 if item[5] == 'male' else 1},  # Or VP can take a dict with a number.
                 {'siblings_onboard': int(item[7])},
                 {'family_members_onboard': int(item[8])},
                 {'fare': float(item[10])},
                 'embarked_' + clean(item[12])
               ]
    title = item[4].split(' ')
    if len(title):
        features.append('title_' + title[1])  # Add a title feature if they have one.
    return {    # VW needs to process a dict with a label and then any number of feature sets.
        'label': int(item[1] == '1'),
        'f': features   # The name 'f' for our feature set is arbitrary, but is the same as the 'ff' above that creates quadratic features.
    }

# Train a logistic regression model on Titanic survival.
# The `run` function will automatically generate a train - test split.
run(logistic_regression(name='Titanic',    # Gives a name to the model file.
                        passes=3,          # How many online passes to do.
                        quadratic='ff',    # Generates automatic quadratic features.
                        nn=5),             # Add a neural network layer with 5 hidden units.
    'titanic/data/titanic.csv',     # File with the data (will automatically be split into random train and test)
    line_function=process_line,     # Function to process each line of the file
    evaluate_function=auc)          # Function to evaluate results
