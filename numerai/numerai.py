from vowpal_platypus import run
from vowpal_platypus.models import logistic_regression
from vowpal_platypus.evaluate_function import log_loss
import argparse
from math import log

parser = argparse.ArgumentParser()
parser.add_argument('--cores')
parser.add_argument('--playground', action='store_true', default=False)
cores = int(parser.parse_args().cores)
playground = parser.parse_args().playground

def compile_train(item):
    item = item.split(',')
    feature_names = ["feature" + str(n) for n in range(1, 22)]
    features = item[0:-1]
    label = -1 if int(item[-1].replace('\n', '')) == 0 else 1
    return {'label': label, 'f': map(lambda x, y: str(x) + ':' + str(y), feature_names, features)}

def compile_predict(item):
    item = item.split(',')
    feature_names = ["feature" + str(n) for n in range(1, 22)]
    features = map(lambda s: s.replace('\n', ''), item[1:])
    return {'f': map(lambda x, y: str(x) + ':' + str(y), feature_names, features)}

model = logistic_regression(name='Numerai', passes=500, cores=cores,
            quadratic='ff', nn=5, l1 = 0.0001, l2 = 0.00001)

if playground:  # For model tuning and such
    results = run(model,
                  filename='numerai/data/numerai_training_data.csv',
                  line_function=compile_train,
                  evaluate_function=log_loss)
    import pdb
    pdb.set_trace()

full_results = run(model,
                   train_filename='numerai/data/numerai_training_data.csv',
                   train_line_function=compile_train,
                   predict_filename='numerai/data/numerai_tournament_data.csv',
                   predict_line_function=compile_predict)
print("Model trained!")
submission_file = open('numerai/data/submission.csv', 'w')
submission_file.write('"t_id","probability"\n')
tournament_file = open('numerai/data/numerai_tournament_data.csv')
tournament_file.readline()
for pred in full_results:
    t_id = str(tournament_file.readline().split(',')[0])
    submission_file.write(t_id + ',' + str((pred + 1) / 2.0) + '\n')
submission_file.flush()
submission_file.close()
print("Submission file written!")
import pdb
pdb.set_trace()
