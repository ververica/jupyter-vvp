from setuptools import setup

DESCRIPTION = "Jupyter VVP: Flink SQL in Jupyter Notebooks via Ververica Platform"
NAME = "jupyter-vvp"
VERSION = '0.1.0'
PACKAGES = ['jupytervvp']
AUTHOR = "Ververica"
AUTHOR_EMAIL = "platform@ververica.com"
URL          = 'https://github.com/ververica/jupyter-vvp'
DOWNLOAD_URL = 'https://github.com/ververica/jupyter-vvp'
LICENSE      = 'Apache License 2.0'

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name=NAME,
      version=VERSION,
      description=DESCRIPTION,
      long_description_content_type="text/markdown",
      long_description=long_description,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      download_url=DOWNLOAD_URL,
      license=LICENSE,
      packages=PACKAGES,
      include_package_data=True,
      package_data={'jupytervvp':['jupytervvp/flinksqlkernel/kernel.json']},
      install_requires=[
          'ipython>=4.0.2',
          'ipywidgets',
          'pandas',
          'ipykernel',
          'requests'
      ])
