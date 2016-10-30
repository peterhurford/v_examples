#!/bin/bash

## Import Titanic data from spreadsheet, impute NAs with median, create title feature, separate into train and test, fit VW to the data, get test AUC.

echo "Splitting..."
tail n +2 ../data/titanic.csv | gshuf | gsplit -d -l 714 /dev/stdin titanic  # 80-20 train-test
echo "Formatting..."
python vw_to_csv.py
echo "Training..."
vw titanic00_s -f model.vw --binary --passes 40 -c -q ff --adaptive --normalized --l1 0.00000001 --l2 0.0000001 -b 24
echo "Predicting..."
vw -d titanic01_s -t -i model.vw -p preds_titanic.txt
echo "Evaluating..."
awk {'print $1'} titanic01_s | paste -d " " /dev/stdin preds_titanic.txt > preds_and_labels.txt
python auc.py
rm model.vw  *.txt titanic0*

# 0.846428571429
# 0.22s
