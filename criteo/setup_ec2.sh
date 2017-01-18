#!/bin/bash
sudo apt-get update
sudo apt-get -y install build-essential
sudo apt-get -y install clang-3.5 llvm
sudo ln -s /usr/bin/clang-3.5 /usr/bin/clang; sudo ln -s /usr/bin/clang++-3.5 /usr/bin/clang++
sudo apt-get -y install libffi-dev libssl-dev libxml2-dev libxslt1-dev libjpeg8-dev zlib1g-dev
sudo apt-get -y install unzip htop iotop bmon parallel
sudo apt-get -y install python-pip python-dev

sudo apt-get -y install libboost-all-dev
git clone https://github.com/JohnLangford/vowpal_wabbit.git && cd vowpal_wabbit
make && sudo make install
cd cluster && sudo make install && cd ../..

git clone https://github.com/peterhurford/vowpal_platypus.git && cd vowpal_platypus && git checkout 1.0.2
sudo python setup.py install && cd ..
sudo -H pip install retrying
