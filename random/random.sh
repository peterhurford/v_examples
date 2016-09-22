seq 1 50 > products.dat
seq -f "%.0f" 1 10000000 > customers.dat
gshuf -r -n 10000000 products.dat | paste -d " " customers.dat /dev/stdin > recs.dat  #11s
