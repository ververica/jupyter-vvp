import unittest

from vvpmagics.variablesubstitution import VvpFormatter, NonExistentVariableException, VariableSyntaxException


class VariableSubstitutionTests(unittest.TestCase):

    def test_substitute_user_variables_works(self):
        input_text = """
        INSERT INTO {{ namespace }}_{resultsTable}
        SELECT * FROM {{ namespace }}_{tableName}
        """
        user_ns = {"resultsTable": "table1", "tableName": "table2"}
        formatter = VvpFormatter(input_text, user_ns)

        expected_output = """
        INSERT INTO {{ namespace }}_table1
        SELECT * FROM {{ namespace }}_table2
        """
        actual_output = formatter.substitute_user_variables()
        assert actual_output == expected_output

    def test_substitute_user_variables_undefined_variable_throws(self):
        input_text = "{var1} sat on {var2}."
        user_ns = {"var1": "The cat"}
        formatter = VvpFormatter(input_text, user_ns)

        with self.assertRaises(NonExistentVariableException) as exception:
            formatter.substitute_user_variables()

        assert exception.exception.variable_name == "var2"

    def test_substitute_user_variables_ambiguous_throws(self):
        input_text = "{var1} sat on {{var2}."
        user_ns = {"var1": "The cat"}
        formatter = VvpFormatter(input_text, user_ns)

        with self.assertRaises(VariableSyntaxException) as exception:
            formatter.substitute_user_variables()

        assert exception.exception.bad_text == "{{var2}"

    def test_prepare_escaped_variables_works_in_simple_case(self):
        input_text = "{{ variable }} and {{ another }} with { ignore }"
        expected = "{{{{ variable }}}} and {{{{ another }}}} with { ignore }"

        assert VvpFormatter._prepare_escaped_variables(input_text) == expected

    def test_prepare_escaped_variables_throws_in_ambiguous_case(self):
        input_text = "{{ good }} and {also_good} and {{bad_because_no_spaces}}"
        user_ns = {"also_good": "dummy_value"}
        formatter = VvpFormatter(input_text, user_ns)

        with self.assertRaises(VariableSyntaxException) as exception:
            formatter.substitute_user_variables()

        assert exception.exception.bad_text == "{{bad_because_no_spaces}"

    def test_substitute_variables_works_in_simple_case(self):
        input_text = "{var1} sat on {var2}."
        escaped_text = input_text
        user_ns = {"var1": "The cat", "var2": "the mat"}

        formatter = VvpFormatter(input_text, user_ns)
        formatted = formatter._substitute_variables(escaped_text)

        assert formatted == "The cat sat on the mat."

    def test_substitute_variables_four_braces_transformed_to_two(self):
        input_text = "{var1} sat on {{ sittingObject }}."
        escaped_text = "{var1} sat on {{{{ sittingObject }}}}."
        user_ns = {"var1": "The cat"}

        formatter = VvpFormatter(input_text, user_ns)
        formatted = formatter._substitute_variables(escaped_text)

        assert formatted == "The cat sat on {{ sittingObject }}."

    def test_get_ambiguous_syntax_returns_nothing_if_correct(self):
        input_text = "{good} and {{ good }}"
        assert VvpFormatter._get_ambiguous_syntax(input_text) is None

    def test_get_ambiguous_syntax_finds_missing_spaces(self):
        test_data = {
            "{{myvar}}": "{{myvar}",  # missing space {
            "{{myvar": "{{myvar",  # missing space; no closing brace match
            "myvar}}": "myvar}}",  # missing space }
            "{ { myvar}}": "{ myvar}}",  # only get up to next brace back
            "{{ myvar}}": "{ myvar}}",  # same even if double braces
            "{ {{ myvar}}": "{ myvar}}"  # matches missing spaces before nesting
        }

        for test_input in test_data.keys():
            assert VvpFormatter._get_ambiguous_syntax(test_input) == test_data[test_input]

    def test_get_ambiguous_syntax_does_not_parse_inside_brackets(self):
        test_data = {
            "{{    myvar }}": None,
            "{{ myvar myvar2 }}": None,
        }

        for test_input in test_data.keys():
            assert VvpFormatter._get_ambiguous_syntax(test_input) == test_data[test_input]

    def test_get_ambiguous_syntax_finds_multiple_braces(self):
        input_text = "{{{ myvar }}}"
        assert VvpFormatter._get_ambiguous_syntax(input_text) == "{{{ myvar }"

    def test_get_ambiguous_syntax_finds_nesting(self):
        test_data = {
            "{ {myvar} }": "{ {myvar}",
            "{{     {myvar } }}": "{     {myvar }"  # inside double braces not parsed, but nesting detected
        }

        for input_data in test_data.keys():
            assert VvpFormatter._get_ambiguous_syntax(input_data) == test_data[input_data]
