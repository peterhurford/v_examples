# Create product file
seq 1 50 > products.dat

# Create customer file
seq -f "%.0f" 1 10000000 > customers.dat

# Randomly sample products and paste them with customers
# to get shuf (called gshuf) on mac, `brew install coreutils`. On Mac, `shuf` is called `gshuf`.
shuf -r -n 10000000 products.dat | paste -d " " customers.dat /dev/stdin > recs.dat  #11s
