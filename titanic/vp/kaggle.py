from vowpal_platypus import logistic_regression, run
import re

def clean(s):
  return " ".join(re.findall(r'\w+', s,flags = re.UNICODE | re.LOCALE)).lower()

def process_line(item, predict=False):
    item = item.split(',')
    if not predict:
        label = item.pop(1)
    features = ['passenger_class_' + clean(item[1]),
                 'last_name_' + clean(item[2]),
                 {'gender': 0 if item[4] == 'male' else 1},
                 {'siblings_onboard': int(item[6])},
                 {'family_members_onboard': int(item[7])},
                 'embarked_' + clean(item[11])]
    title = item[3].split(' ')
    if len(title):
        features.append('title_' + title[0])
    age = item[5]
    if age.isdigit():
        features.append({'age': int(age)})
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
    submission_file.write(str(s[0]) + ',' + str(0 if s[1] <= 0 else 1) + '\n')
submission_file.close()
