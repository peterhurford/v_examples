import numpy
from sklearn import metrics

pred_file = open('titanic/vw/preds_and_labels.txt')
actuals = []
preds = []
for line in pred_file:
    ln = line.split(' ')
    actuals.append(int(float(ln[0]) == 1))
    preds.append(int(float(ln[1]) >= 0))

print "AUC: " + str(metrics.roc_auc_score(numpy.array(actuals), numpy.array(preds)))
