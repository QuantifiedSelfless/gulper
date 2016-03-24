sudo apt-get install \
    libatlas-base-dev gfortran \
    libjpeg-dev libtiff-dev libjasper-dev libpng12-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    build-essential cmake git pkg-config libreadline-dev \
    libboost-python-dev python3 python3-dev python3-pip
    libopenblas-dev liblapack-dev libx11-dev

sudo pip3 install numpy

pushd openface/models
./get-models.sh
popd

if ! python3 -c 'import cv2'; then
    cd /tmp/
    git clone https://github.com/Itseez/opencv.git
    cd opencv
    git checkout 3.1.0
    mkdir build
    cd build
    cmake \
        -D CMAKE_BUILD_TYPE=Release \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D PYTHON3_EXECUTABLE=/usr/bin/python3 \
        .. && \
    make -j && \
    sudo make install
fi

if ! which th; then
    git clone https://github.com/torch/distro.git ~/torch --recursive
    cd ~/torch; bash install-deps;
    ./install.sh
fi
