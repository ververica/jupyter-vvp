import string
from re import search


class VvpFormatter(string.Formatter):
    ambiguous_regexps = [
        "\{\{\S",  # any two left braces followed by a non-whitespace character
        "\S\}\}",  # any non-whitespace character followed by two braces
        "\{\s+\{",  # catch some attempted nesting cases
        "\}\s+\}"  # catch some attempted nesting cases
    ]

    def __init__(self, input_string, user_ns):
        self.input_string = input_string
        self.user_ns = user_ns

    def substitute_user_variables(self):
        ambiguous_syntax = self._get_ambiguous_syntax(self.input_string)
        if ambiguous_syntax:
            raise VariableSyntaxException(ambiguous_syntax,
                                          message="Found the string {}, which is ambiguous or invalid."
                                          .format(ambiguous_syntax))
        escaped_string = self._prepare_escaped_variables(self.input_string)
        return self._substitute_variables(escaped_string)

    @classmethod
    def _get_ambiguous_syntax(cls, input_text):
        for regexp in cls.ambiguous_regexps:
            match = search(regexp, input_text)
            if match:
                return match.group()
        return None

    @staticmethod
    def _prepare_escaped_variables(input_text):
        # string.format() replaces our "{{{{" with "{{" later during substitution
        return input_text.replace("{{ ", "{{{{ ").replace(" }}", " }}}}")

    def _substitute_variables(self, escaped_string):
        try:
            return escaped_string.format(**self.user_ns)
        except KeyError as error:
            raise NonExistentVariableException(error,
                                               message="The variable {} is not defined but is referenced in the cell."
                                               .format(error),
                                               sql=self.input_string)


class NonExistentVariableException(Exception):
    def __init__(self, variable_name, message="", sql=None):
        super(NonExistentVariableException, self).__init__(message)
        self.sql = sql
        self.variable_name = variable_name


class VariableSyntaxException(Exception):
    def __init__(self, bad_text, message="", sql=None):
        super(VariableSyntaxException, self).__init__(message)
        self.bad_text = bad_text
        self.sql = sql
