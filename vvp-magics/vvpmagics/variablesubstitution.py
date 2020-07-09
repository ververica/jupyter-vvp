import re
import string


def _match_forwards(full_string, match, complimentary_regexp):
    start_pos = match.start()
    return re.match(complimentary_regexp, full_string[start_pos:]).group()


def _match_backwards(full_string, match, complimentary_regexp):
    end_pos = match.end()
    matching_text = re.match(complimentary_regexp, full_string[:end_pos + 1][::-1]).group()
    return matching_text[::-1]


# each ambiguous regexp has a corresponding (closing expression, directed matcher) tuple
# for a reverse search the reverse regexp is also reversed
ambiguous_regexps = {
    "\{\{\S": ("[^\}]*\}", _match_forwards),  # any two left braces followed by a non-whitespace character
    "\S\}\}": ("[^\{]*\{", _match_backwards),  # any non-whitespace character followed by two braces
    "\{\s+\{": ("[^\}]*\}", _match_forwards),  # catch some attempted nesting cases
    "\}\s+\}": ("[^\{]*\{", _match_backwards)  # catch some attempted nesting cases
}


class VvpFormatter(string.Formatter):

    @classmethod
    def match_help_expression(cls, regexp, full_string, match):
        complimentary_regexp = ambiguous_regexps[regexp][0]
        match_function = ambiguous_regexps[regexp][1]
        return match_function(full_string, match, complimentary_regexp)

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
        for regexp in ambiguous_regexps.keys():
            match = re.search(regexp, input_text)
            if match:
                return cls.match_help_expression(regexp, input_text, match)
        return None

    @staticmethod
    def _prepare_escaped_variables(input_text):
        # string.format() replaces our "{{{{" with "{{" later during substitution
        return input_text.replace("{{ ", "{{{{ ").replace(" }}", " }}}}")

    def _substitute_variables(self, escaped_string):
        try:
            return escaped_string.format(**self.user_ns)
        except KeyError as error:
            raise NonExistentVariableException(error.args[0],
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
