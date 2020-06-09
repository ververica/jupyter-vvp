"""Magics to connect to vvp."""
__version__ = '0.0.1'

from .getconfig import GetConfig


def load_ipython_extension(ipython):
    ipython.register_magics(GetConfig)
