"""Magics to connect to vvp."""
__version__ = '0.0.1'

from .vvpddlmagics import VvpDdlMagics
from .vvpmagics import VvpMagics


def load_ipython_extension(ipython):
    print("Registering vvpmagics for vvp.")
    ipython.register_magics(VvpMagics)
    ipython.register_magics(VvpDdlMagics)

