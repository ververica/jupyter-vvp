# vvp-magics

[![Build Status](https://travis-ci.com/dataArtisans/vvp-jupyter.svg?token=RGozj1rgTPauwuugxzZx&branch=master)](https://travis-ci.com/dataArtisans/vvp-jupyter)

Experimental support for vvp using IPython Magics commands.

## Packaging

This can be done with
```
python3 setup.py sdist
```
in the same folder as `setup.py`.

The package can be installed locally with 
```
pip3 install ./dist/vvpmagics-x.y.z.tar.gz
```

The package also contains a custom kernel that extends the IPython kernel to provide SQL code completion.
To install the kernel run `jupyter kernelspec install --user flinksqlkernel` after building the package.

## Docker setup

1. Build the vvp-magics package (same as above):
```
python3 setup.py sdist
```
2. Then create the Docker image:
```
docker build . --tag vvp-jupyter:latest
```
This image can be run independently and used to connect to any running VVP instance.
The Docker image comes with the FlinkSql Kernel for code completion pre-installed.

### Docker-compose with VVP
Run docker compose to set the full vvp environment up:
```
docker-compose up vvp-gateway vvp-appmanager vvp-ui vvp-jupyter
```

To log into Jupyter, look into the docker compose output and find a line that looks like this:
```
http://127.0.0.1:8888/?token=814a4f1ef6a10328f25e67aeb9e5d67e381aff0b2fc7ad2b
```

In the notebook use `vvp-gateway` as hostname and `8080` as port.
An example notebook can be found in the `work` folder.
