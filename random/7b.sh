## Create product file (each machine)
seq 1 50 > products.dat

## Create customer file
create_customer_file() {
  seq -f "%.0f" $2 $3 > "customers_$1.dat"
  echo "Finished $1/15 on `date`"
}
# MACHINE A
for i in `seq 0 15`; do
  create_customer_file $i $(($i*109375000)) $(($i*109375000+109374999)) &
done

# MACHINE B
for i in `seq 0 15`; do
  create_customer_file $i $(($i*109375000+1750000001)) $(($i*109375000+109374999+1750000001)) &
done

# MACHINE C
for i in `seq 0 15`; do
  create_customer_file $i $(($i*109375000+3500000001)) $(($i*109375000+109374999+3500000001)) &
done

# MACHINE D
for i in `seq 0 15`; do
  create_customer_file $i $(($i*109375000+5250000001)) $(($i*109375000+109374999+5250000001)) &
done

## Randomly sample products and paste them with customers
## to get shuf (called gshuf) on mac, `brew install coreutils`. On Mac, `shuf` is called `gshuf`.
random_recs() {
  shuf -r -n 109375000 products.dat > "tmp_p_$1"
  paste -d " " "customers_$1.dat" "tmp_p_$1" > "recs_$1.dat"
  rm "tmp_p_$1"
  echo "Finished $1/15 on `date`"
}
date; for i in `seq 0 15`; do
  random_recs $i &
done
# 6m34s
echo recs_*.dat | xargs cat > all_recs.dat #6m5s
rm recs_*

# 12m39s
# $0.71 (0.21 hours @ $0.84*4 cents per hour for 4x c3.4xlarge) for EC2 and $0.02 ($0.003 per GB-day for 4x200GB for 0.009 day) for disk space. --> $0.73
