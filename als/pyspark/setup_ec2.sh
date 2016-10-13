sudo apt-add-repository ppa:webupd8team/java
sudo apt-get update
sudo apt-get -y install htop unzip
sudo apt-get install oracle-java7-installer
wget http://www.scala-lang.org/files/archive/scala-2.11.7.deb
sudo dpkg -i scala-2.11.7.deb
sudo apt-get update
sudo apt-get -y install scala
wget http://d3kbcqa49mib13.cloudfront.net/spark-1.6.1-bin-hadoop2.6.tgz
tar -xzvf spark-1.6.1-bin-hadoop2.6.tgz
sudo apt-get -y install python-pip
sudo pip install numpy
cd spark-1.6.1-bin-hadoop2.6/
cd python/lib/
unzip py4j-0.9-src.zip
unzip pyspark.zip
cd ../../..
echo 'export SPARK_HOME=~/spark-1.6.1-bin-hadoop2.6' >> ~/.bashrc
echo 'export PATH="$PATH:$SPARK_HOME/:$SPARK_HOME/bin/:$SPARK_HOME/python/:$SPARK_HOME/python/lib/"' >> ~/.bashrc
sudo apt-get -y install python-dev
sudo apt-get -y install python-pip
sudo pip install numpy
source ~/.bashrc
run-example SparkPi 10
