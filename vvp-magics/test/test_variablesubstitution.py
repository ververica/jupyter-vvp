import unittest

from IPython.testing.globalipapp import start_ipython

from vvpmagics.variablesubstitution import VvpFormatter, VariableSubstitutionException


class VariableSubstitutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ipython_session = start_ipython()

    def setUp(self):
        self.ipython_session.run_cell(raw_cell='%reset -f')

    def test_substitute_user_variables_works(self):
        ipython_session = self.ipython_session

        input_text = """
        INSERT INTO {{ namespace }}.{resultsTable}
        SELECT * FROM {{ namespace }}.{tableName}
        """
        formatter = VvpFormatter(input_text)
        ipython_session.run_cell(raw_cell='resultsTable="table1"')
        ipython_session.run_cell(raw_cell='tableName="table2"')

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
        ipython_session = self.ipython_session

        input_text = "{var1} sat on {var2}."
        ipython_session.run_cell(raw_cell='var1 = "The cat"')

        formatter = VvpFormatter(input_text)

        with self.assertRaises(VariableSubstitutionException) as exception:
            formatter.substitute_user_variables()
            assert exception.variable_name == "var2"

    def test_substitute_variables_works_in_simple_case(self):
        ipython_session = self.ipython_session

        input_text = "{var1} sat on {var2}."
        escaped_text = input_text
        ipython_session.run_cell(raw_cell='var1 = "The cat"')
        ipython_session.run_cell(raw_cell='var2 = "the mat"')

        formatter = VvpFormatter(input_text)
        formatted = formatter._substitute_variables(escaped_text)

        assert formatted == "The cat sat on the mat."

    def test_substitute_variables_four_braces_transformed_to_two(self):
        ipython_session = self.ipython_session

        input_text = "{var1} sat on {{ sittingObject }}."
        escaped_text = "{var1} sat on {{{{ sittingObject }}}}."
        ipython_session.run_cell(raw_cell='var1 = "The cat"')

        formatter = VvpFormatter(input_text)
        formatted = formatter._substitute_variables(escaped_text)

        assert formatted == "The cat sat on {{ sittingObject }}."
