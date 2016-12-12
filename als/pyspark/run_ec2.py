# pip install boto; pip install paramiko
import boto.ec2
from boto.manage.cmdshell import sshclient_from_instance
import os
import sys
import time
from retrying import retry

@retry(wait_fixed=5000)
def ssh_client(instance, key_path):
    print "s"
    return sshclient_from_instance(instance, key_path, user_name='ubuntu')

@retry(wait_fixed=5000)
def ssh_client_run(ssh_client, cmd):
    print "r"
    ssh_client.run(cmd)

@retry(wait_fixed=5000)
def scp(key_path, dns, source, target=None):
    print "s"
    if target is None:
        target='~/' + source
    os.system('scp -i ' + key_path + ' ' + source + ' ' + 'ubuntu@' + dns + ':' + target)

access_key = os.environ['AWS_ACCESS_KEY_ID']
secret_key = os.environ['AWS_SECRET_ACCESS_KEY']

conn = boto.ec2.connect_to_region("us-west-2",
                                  aws_access_key_id=access_key,
                                  aws_secret_access_key=secret_key)
#reservation = conn.get_all_reservations()[5]
reservation = conn.run_instances('ami-d732f0b7',
                                 key_name='VWProto',
                                 instance_type='m4.10xlarge',
                                 security_groups=['launch-wizard-4'])
instance = reservation.instances[0]
print('Launching instance {}...'.format(instance.id))
while instance.update() != "running":
    sys.stdout.write('w')
    sys.stdout.flush()
    time.sleep(5)

key_path = os.path.join(os.path.expanduser('~/.ssh'), 'VWProto.pem')
volume = conn.create_volume(600, instance.placement, volume_type='io1', iops=10000)
print('Creating volume {}...'.format(volume.id))
while volume.update() != 'available':
    sys.stdout.write('w')
    sys.stdout.flush()
    time.sleep(5)
print('Attaching volume...')
conn.attach_volume(volume.id, instance.id, '/dev/sdx')
while volume.update() != 'in-use':
    sys.stdout.write('w')
    sys.stdout.flush()
    time.sleep(5)
ssh_client = ssh_client(instance, key_path)

print('Queueing apt-get...')
print(ssh_client_run(ssh_client, 'sudo apt-get update'))

print('Installing htop...')
print(ssh_client_run(ssh_client, 'sudo apt-get -y install htop'))
print('htop ready on ubuntu@{}'.format(instance.dns_name))

print('Configuring volume...')
print(ssh_client_run(ssh_client, 'sudo mkdir /vol'))
print(ssh_client_run(ssh_client, 'sudo apt-get -y install xfsprogs'))
print(ssh_client_run(ssh_client, 'sudo mkfs.xfs -q /dev/xvdx'))
print(ssh_client_run(ssh_client, 'sudo mount -o "defaults,noatime,nodiratime" /dev/xvdx /vol'))
print(ssh_client_run(ssh_client, 'sudo chmod 777 /vol'))
print(ssh_client_run(ssh_client, 'export SPARK_LOCAL_DIRS=/vol'))

print("Bootstrapping...")
scp(key_path, instance.dns_name, 'setup_ec2.sh')
print(ssh_client_run(ssh_client, './setup_ec2.sh'))

print("Uploading ml-20m...")
scp(key_path, instance.dns_name, source='~/Downloads/ml-20m.zip', target='ml-20m.zip')
print(ssh_client_run(ssh_client, 'unzip ml-20m.zip'))

print("Running...")
scp(key_path, instance.dns_name, source='runner.py', target='ml-20m/runner.py')
#print(ssh_client.run('cd ml-20m; spark-submit --master local[*] --driver-memory 16G --num-executors 31 --executor-memory 7G --executor-cores 2 --packages com.databricks:spark-csv_2.11:1.5.0 runner.py --partitions 124 --num_ratings 1000000'))
import pdb
pdb.set_trace()
conn.terminate_instances(instance.id)
conn.delete_volume(volume.id)
