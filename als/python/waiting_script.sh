#!/bin/bash
while true; do
  for i in `seq 1 30`; do
    printf "."
    sleep 0.2
  done
  ls -l ALS*pred* --block-size=M | awk '{print $5}' | sed s/M// | awk '{s+=$1} END {printf "%sGB", s/1024}'
  echo ' '
done
