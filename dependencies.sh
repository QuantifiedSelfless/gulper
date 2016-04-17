echo "Installing system packages"

# ubuntu 14.04 ships with an OOLLLDDD version of cmake
sudo add-apt-repository -y ppa:george-edison55/cmake-3.x

#ubuntu 14.04 has no easy way of install python3.5
sudo add-apt-repository -y ppa:fkrull/deadsnakes

sudo apt update
sudo apt install \
    libatlas-base-dev gfortran \
    libjpeg-dev libtiff5-dev libjasper-dev libpng12-dev \
    libavcodec-dev libavformat-dev libswscale-dev libv4l-dev \
    build-essential cmake git pkg-config libreadline-dev \
    libboost-python-dev python3.5 python3.5-dev \
    libopenblas-dev liblapack-dev libx11-dev || exit 0
sleep 5

if ! command -v "pip3.5" > /dev/null; then
    echo "Installing pip-3.5"
    curl -o /tmp/get-pip.py https://bootstrap.pypa.io/get-pip.py
    sudo python3.5 /tmp/get-pip.py
    rm -rf /tmp/get-pip.py
    sleep 5
fi

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
    sudo pip3.5 install numpy
    sleep 5

    tempdir=$( mktemp -d --suffix='.opencv' )
    pushd ${tempdir}
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
    rm -rf ${tempdir}
    popd
fi

if [ ! -d ~/torch ]; then
    git clone https://github.com/torch/distro.git ~/torch --recursive
    pushd ~/torch; 
    bash install-deps;
    ./install.sh -b
    source ~/.bashrc
    luarocks install dpnn
    popd
fi

echo "Getting python packages"
sudo pip3.5 install -U -r requirements.txt
