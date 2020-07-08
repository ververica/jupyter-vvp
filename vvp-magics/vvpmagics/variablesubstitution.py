import string

from IPython import get_ipython


class VvpFormatter(string.Formatter):

    def __init__(self, input_string, user_ns):
        self.input_string = input_string
        self.user_ns = user_ns

    def substitute_user_variables(self):
        escaped_string = self._prepare_escaped_variables(self.input_string)
        return self._substitute_variables(escaped_string)

    @staticmethod
    def _prepare_escaped_variables(input_text):
        return input_text.replace("{{ ", "{{{{ ").replace(" }}", " }}}}")

    def _substitute_variables(self, escaped_string):
        try:
            return escaped_string.format(**self.user_ns)
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
