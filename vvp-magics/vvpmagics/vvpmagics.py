from IPython.core.magic import (Magics, magics_class, line_magic)

print('Loading vvp-vvpmagics.')


@magics_class
class VvpMagics(Magics):

    vvpUrl = "http://localhost:8000"

    @line_magic
    def getConfig(self, line):
        # TODO #2: Do the connection
        return "Will return the config from {}/config.json .".format(self.vvpUrl)

