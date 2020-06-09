from IPython.core.magic import (Magics, magics_class, line_magic)

print('Loading vvp-magics.')


@magics_class
class GetConfig(Magics):
    @line_magic
    def getConfig(self, line):
        # TODO #2: Do the connection
        return "Will return the config."
