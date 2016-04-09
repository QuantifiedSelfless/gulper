echo "Installing system packages"
sudo apt-get install \
    libatlas-base-dev gfortran \
    libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    build-essential cmake git pkg-config libreadline-dev \
    libboost-python-dev python3 python3-dev python3-pip \
    libopenblas-dev liblapack-dev libx11-dev || exit 0
sleep 5

echo "Getting openface models"
git submodule init
git submodule update
pushd openface/models
./get-models.sh
popd
sleep 5

memory=$( free -t | tail -n 1 | awk '{ print $2 }' )
if [ $memory -lt 2048 ]; then
    echo "At least 2GB of RAM+SWAP is necissary to install opencv and dlib"
    exit 0
fi

if ! python3.5 -c 'import cv2'; then
    echo "Installing numpy"
    sudo pip3 install numpy
    sleep 5

    tempdir=$( mktemp -d --suffix='.opencv' )
    cd ${tempdir}
    git clone https://github.com/Itseez/opencv.git
    cd opencv
    git checkout 3.1.0
    mkdir build
    cd build
    cmake \
        -D CMAKE_BUILD_TYPE=Release \
        -D CMAKE_INSTALL_PREFIX=/usr/local \
        -D PYTHON3_EXECUTABLE=/usr/bin/python3.5 \
        .. && \
    make && \
    sudo make install || exit 0
fi

if [ ! -d ~/torch ]; then
    git clone https://github.com/torch/distro.git ~/torch --recursive
    cd ~/torch; bash install-deps;
    ./install.sh -b
fi

echo "Getting python packages"
sudo pip3 install -U -r requirements.txt
