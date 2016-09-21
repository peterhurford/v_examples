mkdir dev; cd ~/dev
sudo apt-get update
sudo apt-get install build-essential
sudo apt-get install clang-3.5 llvm
sudo ln -s /usr/bin/clang-3.5 /usr/bin/clang; sudo ln -s /usr/bin/clang++-3.5 /usr/bin/clang++
sudo apt-get install libboost-all-dev
sudo apt-get install git
sudo apt-get install unzip
sudo apt-get install htop
git clone https://github.com/JohnLangford/vowpal_wabbit.git
cd vowpal_wabbit
make
sudo make install
cd ..

# Also be sure to scp up the zip file
