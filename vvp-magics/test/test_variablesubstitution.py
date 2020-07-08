import unittest

from vvpmagics.variablesubstitution import VvpFormatter, VariableSubstitutionException


class VariableSubstitutionTests(unittest.TestCase):

    def test_substitute_user_variables_works(self):
        input_text = """
        INSERT INTO {{ namespace }}.{resultsTable}
        SELECT * FROM {{ namespace }}.{tableName}
        """
        user_ns = {"resultsTable": "table1", "tableName": "table2"}
        formatter = VvpFormatter(input_text, user_ns)

        expected_output = """
        INSERT INTO {{ namespace }}.table1
        SELECT * FROM {{ namespace }}.table2
        """
        actual_output = formatter.substitute_user_variables()
        assert actual_output == expected_output

    def test_prepare_escaped_variables_works_in_simple_case(self):
        input_text = "{{ variable }} and {{ another }} with { ignore }"
        expected = "{{{{ variable }}}} and {{{{ another }}}} with { ignore }"

        assert VvpFormatter._prepare_escaped_variables(input_text) == expected

    def test_substitute_user_variables_undefined_variable_throws(self):
        input_text = "{var1} sat on {var2}."
        user_ns = {"var1": "The cat"}
        formatter = VvpFormatter(input_text, user_ns)

        with self.assertRaises(VariableSubstitutionException) as exception:
            formatter.substitute_user_variables()
            assert exception.variable_name == "var2"

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
