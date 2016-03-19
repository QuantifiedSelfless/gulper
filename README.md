# gulper

## Installation

First install system dependencies

```
# apt install libboost-python-dev python3 python3-pip
```

Then python dependencies

```
# pip install -U -r requirements.txt
```

Decrypt the config file

```
$ python3 config_packer.py decrypt config.conf.enc > config.conf
```

and finally, run!

```
$ python3 api.py
```
