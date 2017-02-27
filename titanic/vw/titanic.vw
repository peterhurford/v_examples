#!/bin/bash

## Raw VW example on Titanic data.
## Run with `./titanic/vw/titanic.vw`.

## Import Titanic data from spreadsheet, impute NAs with median, create title feature, separate into train and test, fit VW to the data, get test AUC.

echo "Splitting..."
tail -n +2 titanic/data/titanic.csv | gshuf | gsplit -d -l 714 /dev/stdin titanic/vw/titanic  # 80-20 train-test
echo "Formatting..."
python titanic/vw/vw_to_csv.py
echo "Training..."
vw titanic/vw/titanic00_s -f titanic/vw/model.vw --binary --passes 3 -c -q ff --l1 0.001
echo "Predicting..."
vw -d titanic/vw/titanic01_s -t -i titanic/vw/model.vw -p titanic/vw/preds_titanic.txt
echo "Evaluating..."
awk {'print $1'} titanic/vw/titanic01_s | paste -d " " /dev/stdin titanic/vw/preds_titanic.txt > titanic/vw/preds_and_labels.txt
python titanic/vw/auc.py
rm titanic/vw/model.vw  titanic/vw/*.txt titanic/vw/titanic0*
