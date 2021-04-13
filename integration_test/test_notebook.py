import os
import unittest

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

SKIP_INTEGRATION_TESTS = os.environ.get('SKIP_INTEGRATION_TESTS', False)


def run_notebook(notebook_path):
    nb_name, _ = os.path.splitext(os.path.basename(notebook_path))
    dirname = os.path.dirname(notebook_path)

    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    proc = ExecutePreprocessor(timeout=600)
    proc.allow_errors = True

    proc.preprocess(nb, {'metadata': {'path': '/'}})
    output_path = os.path.join(dirname, '{}_all_output.ipynb'.format(nb_name))

    with open(output_path, mode='wt') as f:
        nbformat.write(nb, f)
    errors = []
    for cell in nb.cells:
        for output in cell.get('outputs', []):
            if output.output_type == 'error' or (output.output_type == 'stream' and output.name == 'stderr'):
                errors.append(output)
    return nb, errors


@unittest.skipIf(SKIP_INTEGRATION_TESTS, 'Requires locally running VVP backend.')
class IntegrationTest(unittest.TestCase):

    def test_connect_notebook(self):
        notebook_path = os.path.dirname(__file__) + "/../example_notebooks/"
        files = [item for item in os.listdir(notebook_path) if os.path.isfile(os.path.join(notebook_path, item))]
        notebooks = filter(lambda x: x.endswith(".ipynb"), files)
        for i, notebook in enumerate(notebooks, start=1):
            print("{}.: Running notebook '{}'.".format(i, notebook))
            nb, errors = run_notebook(os.path.join(notebook_path, notebook))
            self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
