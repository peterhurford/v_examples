#!/usr/bin/env bash

readonly SPARK_VERSION='spark-1.6.1-bin-hadoop2.6'
sudo apt-get update
sudo apt-get -y install default-jre
sudo apt-get -y install default-jdk
sudo apt-get -y install htop iotop bmon unzip python-pip || (echo "Installation failed" && exit)
sudo apt-get -y install oracle-java7-installer || (echo "Installation failed" && exit)
sudo apt-get -y install scala || (echo "Installation failed" && exit)
wget "http://d3kbcqa49mib13.cloudfront.net/$SPARK_VERSION.tgz" && tar -xzvf "$SPARK_VERSION.tgz"

sudo pip install numpy
sudo pip install psutil
cd "$SPARK_VERSION"
cd python/lib/
unzip py4j*.zip
unzip pyspark.zip
cd ../../..
echo "export SPARK_HOME=~/$SPARK_VERSION" >> ~/.bashrc
echo 'export PATH="$PATH:$SPARK_HOME/:$SPARK_HOME/bin/:$SPARK_HOME/python/:$SPARK_HOME/python/lib/"' >> ~/.bashrc
sudo apt-get -y install python-dev python-pip || (echo "Installation failed" && exit)
sudo pip install numpy

# Raise ulimit
sudo tee -a /etc/security/limits.conf <<EOF
*       soft  nofile  20000
*       hard  nofile  20000
EOF

source ~/.bashrc
run-example SparkPi 10
