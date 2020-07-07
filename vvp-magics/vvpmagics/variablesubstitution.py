import string

from IPython import get_ipython


class VvpFormatter(string.Formatter):

    def __init__(self, input_string):
        self.input_string = input_string

    def substitute_variables(self):
        try:
            session = get_ipython()
            return self.input_string.format(**session.user_ns)
        except KeyError as error:
            raise VariableSubstitutionException(error,
                                                message="The variable {} is not defined but is referenced in the cell."
                                                .format(error),
                                                sql=self.input_string)


class VariableSubstitutionException(Exception):
    def __init__(self, variable_name, message="", sql=None):
        super(VariableSubstitutionException, self).__init__(message)
        self.sql = sql
        self.variable_name = variable_name
