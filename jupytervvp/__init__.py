"""Magics to connect to vvp."""
__version__ = '0.0.1'

from .jupytervvp import VvpMagics


def load_ipython_extension(ipython):
    print("Registering jupytervvp for vvp.")
    ipython.register_magics(VvpMagics)

