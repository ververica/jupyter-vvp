# vvp-magics

[![Build Status](https://travis-ci.com/ververica/jupyter-vvp.svg?token=RGozj1rgTPauwuugxzZx&branch=master)](https://travis-ci.com/ververica/jupyter-vvp)

Jupyter support for Ververica Platform using IPython Magics commands.

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
docker build . --tag jupyter-vvp:latest
```
This image can be run independently and used to connect to any running Ververica Platform instance.
The Docker image comes with the FlinkSql Kernel for code completion pre-installed.

## Publishing

The jupyter-vvp package is published to PyPi. The script `dev/scripts/publish.sh` will do everything required to publish the package. You will need to provide the PyPi username and password.

In order to test the upload the TestPyPi index can be used, the command to upload is `twine upload --repository testpypi dist/*`. Note that there is a different password for the Test PyPi, the username is the same.

## Development

### Testing

Unit tests should be used to test functionality whereever possible.
If integration with Ververica Platform needs to be tested, integration tests should be used.
One of the integration tests executes example notebooks, so those should also be updated when any changes are made.
The integration tests are currently not executed by travis, and only run locally.

### Versioning

Jupyter-VVP is versioned independently of Ververica Platform, compatibility with Ververica Platform versions should be indicated in the readme.
Versioning follows the semantic versioning scheme, major.minor.patch.
Major versions indicate bigger, possibly breaking, changes.
Minor versions indicate non-breaking updates.
Patch versions are only bugfix and stability updates.
