import unittest

from IPython.testing.globalipapp import start_ipython

from vvpmagics.variablesubstitution import VvpFormatter, VariableSubstitutionException


class VariableSubstitutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ipython_session = start_ipython()

    def setUp(self):
        self.ipython_session.run_cell(raw_cell='%reset -f')

    def test_two_simple_variables_substituted(self):
        ipython_session = self.ipython_session

        input_text = "{var1} sat on {var2}."
        ipython_session.run_cell(raw_cell='var1 = "The cat"')
        ipython_session.run_cell(raw_cell='var2 = "the mat"')

        formatter = VvpFormatter(input_text)
        formatted = formatter.substitute_variables()

        assert formatted == "The cat sat on the mat."

    def test_undefined_variable_throws(self):
        ipython_session = self.ipython_session

        input_text = "{var1} sat on {var2}."
        ipython_session.run_cell(raw_cell='var1 = "The cat"')

        formatter = VvpFormatter(input_text)

        with self.assertRaises(VariableSubstitutionException) as exception:
            formatter.substitute_variables()
            assert exception.variable_name == "var2"

    def test_four_braces_transformed_to_two(self):
        ipython_session = self.ipython_session

        input_text = "{var1} sat on {{{{ sittingObject }}}}."
        ipython_session.run_cell(raw_cell='var1 = "The cat"')

        formatter = VvpFormatter(input_text)
        formatted = formatter.substitute_variables()

        assert formatted == "The cat sat on {{ sittingObject }}."
