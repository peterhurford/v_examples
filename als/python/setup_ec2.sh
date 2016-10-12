#!/bin/bash
sudo apt-get update
sudo apt-get -y install build-essential
sudo apt-get -y install clang-3.5 llvm
sudo ln -s /usr/bin/clang-3.5 /usr/bin/clang; sudo ln -s /usr/bin/clang++-3.5 /usr/bin/clang++
sudo apt-get -y install libboost-all-dev
sudo apt-get -y install git
sudo apt-get -y install unzip htop parallel
git clone https://github.com/JohnLangford/vowpal_wabbit.git; cd vowpal_wabbit; make; sudo make install; cd ..
sudo apt-get -y install libblas-dev liblapack-dev libatlas-base-dev gfortran
sudo apt-get -y install python-pip
sudo pip install cython
sudo pip install numpy
sudo pip install scipy
git clone https://github.com/peterhurford/vowpal_porpoise.git; cd vowpal_porpoise; sudo python setup.py install; cd ..

# Also be sure to scp up the zip file and the runner
