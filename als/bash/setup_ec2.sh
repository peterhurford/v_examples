sudo apt-get update
sudo apt-get -y install build-essential
sudo apt-get -y install clang-3.5 llvm
sudo ln -s /usr/bin/clang-3.5 /usr/bin/clang; sudo ln -s /usr/bin/clang++-3.5 /usr/bin/clang++
sudo apt-get -y install libboost-all-dev
sudo apt-get -y install git
sudo apt-get -y install unzip htop parallel
git clone https://github.com/JohnLangford/vowpal_wabbit.git; cd vowpal_wabbit; make; sudo make install; cd ..

# Also be sure to scp up the zip file
