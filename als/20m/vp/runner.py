from vowpal_platypus import run
from vowpal_platypus.models import als
from vowpal_platypus.evaluation import rmse
import argparse
import os
from datetime import datetime

start = datetime.now()
print('...Starting at ' + str(start))

print("Setting up...")
start = datetime.now()
parser = argparse.ArgumentParser()
parser.add_argument('--cores')
cores = int(parser.parse_args().cores)

ratings_file = open('ratings_.csv', 'r')
movie_file = open('movies.csv', 'r')
user_file = open('users.csv', 'r')
movie_ids = [movie.split(',')[0] for movie in list(movie_file.read().splitlines())]
user_ids = [user.split(',')[0] for user in list(user_file.read().splitlines())]
movie_ids.pop(0) # Throw out headers
user_ids.pop(0)

ratings = compile_ratings(ratings_file)

movie_file.close()
user_file.close()
ratings_file.close()

def compile_rating(item):
    item = item.split('::')
    rating = item[2]
    user_id = item[0]
    movie_id = item[1]
    return {'label': rating, 'c': user_id, 'p': movie_id}

model = als(name='ALS', passes=10, cores=cores,
            quadratic='cp', rank=10,
            l2=0.01, learning_rate=0.015, decay_learning_rate=0.97, power_t=0)


def train_model(model):
    core = model.params.get('node', 0)
    filename = 'als/1m/data/ratings.dat' + (str(core) if core >= 10 else '0' + str(core))
    num_lines = sum(1 for line in open(audience_filename, 'r'))
    log.info('{}: Loading {} lines...'.format(audience_filename, num_lines))
    i = 0
    curr_done = 0
    with open(filename, 'r') as filehandle:
        with model.training():
            while True:
                item = filehandle.readline()
                if not item:
                    break
                i += 1
                done = int(i / float(num_lines) * 100)
                if done - curr_done > 1:
                    log.info('{}: training done {}%'.format(audience_filename, done))
                    curr_done = done
                vw_item = compile_rating(item)
                model.push_instance(vw_item)

model = daemon(model, port=20168)

def rec_with_model(core):
    user_id_pool = filter(lambda x: int(x) % train_cores == core, user_ids)
    i = 0
    curr_done = 0
    with open(filename, 'r') as filehandle:
        available_products = [p for p in products.items() if p[1].get('available') is True or p[1].get('available') is None]
        while True:
            item = filehandle.readline()
            if not item:
                break
            i += 1
            done = int(i / float(num_lines) * 100)
            if done - curr_done > 1:
                log.info('{}: recs done {}%'.format(audience_filename, done))
                curr_done = done
            customer_id, audiences = process_audience(item)
            if any(map(lambda x: x in target_audiences, audiences)):
                if actions.get(customer_id) is not None:
                    vw_items = []
                    for product_id, product in available_products:
                        vw_items.append(vw_line_fn(audiences, customer_id, product_id, predict=True))
                    preds = daemon_predict(model, vw_items)
                    product_ids = [p[0] for p in available_products]
                    recs[customer_id] = sorted(zip(preds, product_ids), reverse=True)[0][1]  # Sorts by prediction, takes highest predicted product, gets product ID.
    log.info('{}: Returning data to driver...'.format(audience_filename))
    return recs

def evaluate_model(model):
results = run(model,
              'als/20m/data/ratings.dat',
              line_function=compile_rating,
              evaluate_function=rmse,
              header=False)

rmse = 'RMSE: ' + str(rmse(results))
end = datetime.now()
time = 'Time: ' + str((end - start).total_seconds()) + ' sec'
speed = 'Speed: ' + str((end - start).total_seconds() * 1000000 / float(num_ratings)) + ' mcs/row'





def train_on_core(core):
    vw = vw_instances[core]
    user_id_pool = filter(lambda x: int(x) % train_cores == core, user_ids)
    vw.start_training()
    for user_id in user_id_pool:
        for movie_id, rating in ratings[user_id].iteritems():
            vw_item = rating + ' |u ' + user_id + ' |i ' + movie_id
            vw.push_instance(vw_item)
    vw.close_process()
    return None

@retry(wait_fixed=1000)
def netcat(hostname, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, port))
    s.sendall(content)
    s.shutdown(socket.SHUT_WR)
    data = []
    while True:
        datum = s.recv(1024)
        if datum == '':
            break
        datum = datum.split('\n')
        for dat in datum:
            if dat != '':
                dat = float(dat)
                if 5 >= dat >= 0:
                    data.append(dat)
    s.close()
    return data
    
def daemon(core):
    port = core + 4040
    train_model = vw_instances[core % train_cores].get_model_file()
    initial_moniker = vw_instances[core % train_cores].handle
    return VW(moniker=initial_moniker, daemon=True, old_model=train_model, holdout_off=True, quiet=True, port=port, num_children=2).start_predicting()

def compile_ratings(ratings_file):
    ratings = {}
    while True:
        item = ratings_file.readline()
        if not item:
            break
        item = item.split(',')
        rating = item[2]
        user_id = item[0]
        movie_id = item[1]
        if ratings.get(user_id) is None:
            ratings[user_id] = {} 
        ratings[user_id][movie_id] = rating
    return ratings

def rec_for_user(core):
    rfile = rec_files[core]
    port = 4040 + core
    user_id_pool = filter(lambda x: int(x) % predict_cores == core, user_ids)
    for user_id in user_id_pool:
        unseen_movie_ids = list(set(movie_ids) - set(ratings[user_id].values()))
        vw_items = ''.join(map(lambda m: '|u ' + user_id + ' |i ' + m + '\n', unseen_movie_ids))
        print('Connecting to port %i...' % port)
        preds = netcat('localhost', port, vw_items)
        user_recs = [list(a) for a in zip(preds, unseen_movie_ids)]
        user_recs.sort(reverse=True)
        rfile.write(str({'user': user_id,
                        'products': map(lambda x: x[1], user_recs[:10])}) + '\n')
    rfile.flush()
    return None

def evaluate_on_core(core):
    port = 4040 + core
    user_id_pool = filter(lambda x: int(x) % predict_cores == core, user_ids)
    all_preds = []
    for user_id in user_id_pool:
        vw_items = ''
        user_ratings = []
        if ratings.get(user_id) is not None:
            for movie_id, rating in ratings[user_id].iteritems():
                vw_items += '|u ' + user_id + ' |i ' + movie_id + '\n'
                user_ratings.append(float(rating))
            print('Connecting to port %i...' % port)
            preds = netcat('localhost', port, vw_items)
            all_preds.append(zip(preds, user_ratings))
    all_preds = sum(all_preds, [])
    return sum(map(lambda x: (float(x[0]) - float(x[1])) ** 2, all_preds)) / len(all_preds)



print("Formating data...")
os.system("head -n {} {}ratings.csv | tail -n +2 > {}ratings_.csv".format(num_ratings + 1, volume, volume)) # +1 to not trim header
os.system("tail -n +2 " + volume + "ratings_.csv | awk -F\",\" '{print $1}' | uniq > " + volume + "users.csv")

ratings_file = open('{}ratings_.csv'.format(volume), 'r')
movie_file = open('{}movies.csv'.format(volume), 'r')
user_file = open('{}users.csv'.format(volume), 'r')
movie_ids = [movie.split(',')[0] for movie in list(movie_file.read().splitlines())]
user_ids = [user.split(',')[0] for user in list(user_file.read().splitlines())]
movie_ids.pop(0) # Throw out headers
user_ids.pop(0)

ratings = compile_ratings(ratings_file)

movie_file.close()
user_file.close()
ratings_file.close()
setup_done = datetime.now()

print("Booting models...")
if train_cores > 1:
    os.system("spanning_tree")
    vw_instances = [vw_model(n, volume) for n in range(train_cores)]
else:
    vw_instances = [vw_model(0, volume, parallel=False)]

if not evaluate_only:
    print("Jamming some train on {} cores...".format(train_cores))
    if train_cores > 1:
        pool = Pool(train_cores)
        pool.map(train_on_core, range(train_cores))
    else:
        train_on_core(0)
    training_done = datetime.now()

    print("Spooling predictions on {} cores...".format(predict_cores))
    train_model = vw_instances[0].get_model_file()
    initial_moniker = vw_instances[0].handle

    rec_files = [open('{}/py_recs'.format(volume) + str(i) + '.dat', 'w') for i in range(predict_cores)]

    if predict_cores > 1:
        daemons = [daemon(core) for core in random.sample(range(predict_cores), predict_cores)]
        pool = Pool(predict_cores)
        pool.map(rec_for_user, range(predict_cores))
    else:
        daemons = [daemon(0)]
        rec_for_user(0)

    for f in rec_files:
        f.close()
    os.system('cat {}/py_recs* > {}/all_py_recs.csv'.format(volume, volume))
    recs_done = datetime.now()

if evaluate:
    print('Evaluating...')
    if evaluate == 'ib':
        print('Shuffling for ib evaluate...')
        if op_sys == 'mac':
            shuf = 'gshuf'
            split = 'gsplit'
        else:
            shuf = 'shuf'
            split = 'split'
        os.system("{} ratings_.csv > ratings__.csv; mv ratings__.csv ratings_.csv".format(shuf))
    os.system("{} -d -l {} ratings_.csv".format(split, int(num_ratings * 0.9)))
    os.system("mv x00 ratings_train.csv; mv x01 ratings_test.csv")
    ratings_file = open('ratings_train.csv', 'r')
    ratings = compile_ratings(ratings_file)
    if train_cores > 1:
        pool = Pool(train_cores)
        pool.map(train_on_core, range(train_cores))
    else:
        train_on_core(0)

    ratings = {}
    ratings_file = open('ratings_test.csv', 'r')
    ratings = compile_ratings(ratings_file)

    if predict_cores > 1:
        daemons = [daemon(core) for core in random.sample(range(predict_cores), predict_cores)]
        pool = Pool(predict_cores)
        rmses = pool.map(evaluate_on_core, range(predict_cores))
        rmse = (sum(rmses) / predict_cores) ** 0.5
    else:
        daemons = [daemon(0)]
        rmse = evaluate_on_core(0)
    print("RMSE: " + str(rmse))
    evaluate_done = datetime.now()

print("Spinning down server...")
if train_cores > 1:
    os.system("killall spanning_tree")
for port in range(4040, 4040 + predict_cores):
    print("Spinning down port %i" % port)
    os.system("pkill -9 -f 'vw.*--port %i'" % port)

print("Timing...")
print("Set up in " + str(setup_done - start))
if not evaluate_only:
    print("Training in " + str(training_done - setup_done))
    print("Reccing in " + str(recs_done - training_done))
    if evaluate:
        print("Evaluating in: " + str(evaluate_done - recs_done))
        print("Total (without evaluate): " + str(recs_done - start))
        print("Total: " + str(evaluate_done - start))
    else:
        print("Total: " + str(recs_done - start))
else:
    print("Evaluating in: " + str(evaluate_done - setup_done))
    print("Total: " + str(evaluate_done - start))
