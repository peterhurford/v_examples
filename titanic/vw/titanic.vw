#!/bin/bash

## Import Titanic data from spreadsheet, impute NAs with median, create title feature, separate into train and test, fit VW to the data, get test AUC.

echo "Splitting..."
tail -n +2 titanic/data/titanic.csv | gshuf | gsplit -d -l 714 /dev/stdin titanic/vw/titanic  # 80-20 train-test
echo "Formatting..."
python titanic/vw/vw_to_csv.py
echo "Training..."
vw titanic/vw/titanic00_s -f titanic/vw/model.vw --binary --passes 40 -c -q ff --adaptive --normalized --l1 0.00000001 --l2 0.0000001 -b 24
echo "Predicting..."
vw -d titanic/vw/titanic01_s -t -i titanic/vw/model.vw -p titanic/vw/preds_titanic.txt
echo "Evaluating..."
awk {'print $1'} titanic/vw/titanic01_s | paste -d " " /dev/stdin titanic/vw/preds_titanic.txt > titanic/vw/preds_and_labels.txt
python titanic/vw/auc.py
rm titanic/vw/model.vw  titanic/vw/*.txt titanic/vw/titanic0*

# 0.846428571429
# 0.22s
