#!/bin/bash
user_count=$(wc -l users.csv | awk {'print $1'})
while true; do
  for i in `seq 1 30`; do
    printf "."
    sleep 0.2
  done
  length=$(wc -l *recs* | tail -n 1 | awk {'print $1'})
  echo "$length/$user_count*100" | bc -l
done
