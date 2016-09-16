import csv
import json

products = json.loads(open('~/Downloads/2016-09-16-14-32-34/part-00000', 'r'))
import pdb
pdb.set_trace()
csv_file = csv.writer(open('products.csv', 'wb+'))
