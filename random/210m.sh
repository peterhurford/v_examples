# Create product file
seq 1 50 > products.dat

# Create customer file
seq -f "%.0f" 1 210000000 > customers.dat

# Randomly sample products and paste them with customers
# to get shuf (called gshuf) on mac, `brew install coreutils`. On Mac, `shuf` is called `gshuf`.
random_recs() {
  shuf -r -n 26250000 products.dat > "tmp_p_$1"
  tail -n +$(($1*26250000)) customers.dat | head -n 26250000 > "tmp_c_$1"
  paste -d " " "tmp_c_$1" "tmp_p_$1" > "recs_$1.dat"
  rm "tmp_c_$1" "tmp_p_$1"
  echo "Finished $1/7 on `date`"
}
date; for i in `seq 0 7`; do
  random_recs $i &
done
# 2m51s
echo recs_*.dat | xargs cat > all_recs.dat #5s
rm recs_*

#2m56s
# $0.01 (0.05 hours @ $0.24 cents per hour for m4.xlarge) for EC2
