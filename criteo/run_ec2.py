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
# TODO: Be able to recover without booting up a new instance.
reservation = conn.get_all_reservations()[1]
# reservation = conn.run_instances('ami-d732f0b7',
#                                  key_name='VWProto',
#                                  instance_type='m4.16xlarge',
#                                  security_groups=['launch-wizard-4'])
instance = reservation.instances[0]
print('Launching instance {}...'.format(instance.id))
while instance.update() != "running":
    sys.stdout.write('w')
    sys.stdout.flush()
    time.sleep(5)

key_path = os.path.join(os.path.expanduser('~/.ssh'), 'VWProto.pem')
volume = conn.create_volume(400, instance.placement, volume_type='io1', iops=20000)
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

print('Queueing apt-get...')
ssh_client = ssh_client(instance, key_path)
print(ssh_client.run('sudo apt-get update'))

print('Installing htop...')
print(ssh_client.run('sudo apt-get -y install htop'))
print('htop ready on ubuntu@{}'.format(instance.dns_name))

print("Bootstrapping...")
scp(key_path, instance.dns_name, 'setup_ec2.sh')
print(ssh_client.run('./setup_ec2.sh'))

print("Mounting volume...")
print(ssh_client.run('sudo mkdir /vol'))
import pdb
pdb.set_trace()
print(ssh_client.run('sudo apt-get -y install xfsprogs'))
print(ssh_client.run('sudo mkfs.xfs -q /dev/xvdx'))
print(ssh_client.run('sudo mount -o "defaults,noatime,nodiratime" /dev/xvdx /vol'))
print(ssh_client.run('sudo chmod 777 /vol'))

print("Uploading ml-20m...")
scp(key_path, instance.dns_name, source='display.zip', target='/vol/display.zip')
print(ssh_client.run('unzip /vol/display.zip'))
import pdb
pdb.set_trace()
conn.terminate_instances(instance.id)
conn.delete_volume(volume.id)
