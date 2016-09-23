sudo apt-get update
sudo apt-get install build-essential
tar -xvf coreutils-8.25.tar.xz
cd coreutils-8.25/
./configure --prefix=/usr/local
make
sudo make install; cd ..
