from vowpal_platypus import run
from vowpal_platypus.models import logistic_regression
from vowpal_platypus.utils import clean

def process_line(item, predict=False):
    item = item.split(',')
    if not predict:
        label = item.pop(1)
    features = ['passenger_class_' + clean(item[1]),
                 {'gender': 0 if item[4] == 'male' else 1},
                 {'siblings_onboard': int(item[6])},
                 {'family_members_onboard': int(item[7])},
                 'embarked_' + clean(item[11])]
    last_name = clean(item[2]).split(' ')
    if len(last_name):
        features.append('last_' + last_name[0])
    title = clean(item[3]).split(' ')
    if len(title):
        features.append('title_' + title[0])
    try:
        features.append({'age': float(item[5])})
    except:
        pass
    fare = item[9]
    if fare.isdigit():
        features.append({'fare': int(fare)})
    if predict:
        return {'f': features}
    else:
        return {'label': 1 if label == '1' else -1, 'f': features}

results = (logistic_regression(name='Titanic',
                               passes=3,
                               quadratic='ff',
                               nn=5)
            .train_on('titanic/data/kaggle/train.csv',
                      line_function=process_line,
                      header=True)
            .predict_on('titanic/data/kaggle/test.csv',
                        line_function=lambda l: process_line(l, predict=True)))
ids = range(892, len(results) + 892)
submission = zip(ids, results)
submission_file = open('titanic/data/kaggle/submission.csv', 'w')
submission_file.write('PassengerId,Survived\n')
for s in submission:
    submission_file.write(str(s[0]) + ',' + str(0 if s[1] <= 0.5 else 1) + '\n')
submission_file.close()
