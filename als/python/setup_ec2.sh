sudo apt-get update
sudo apt-get install build-essential
sudo apt-get install clang-3.5 llvm
sudo ln -s /usr/bin/clang-3.5 /usr/bin/clang; sudo ln -s /usr/bin/clang++-3.5 /usr/bin/clang++
sudo apt-get install libboost-all-dev
sudo apt-get install git
sudo apt-get install unzip htop parallel
git clone https://github.com/JohnLangford/vowpal_wabbit.git; cd vowpal_wabbit; make; sudo make install; cd ..
sudo apt-get install python-pip
sudo pip install cython
sudo pip install numpy
sudo pip install scipy
git clone https://github.com/peterhurford/vowpal_porpoise.git; cd vowpal_porpoise; python setup.py install; cd ..

# Also be sure to scp up the zip file and runner.py
