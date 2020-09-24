import json
import unittest

from jupytervvp.jsonconversion import json_convert_to_dataframe


class JsonTests(unittest.TestCase):
    def test_json_conversion(self):
        json_string = """{"result": "RESULT_SUCCESS_WITH_ROWS",
 "resultTable": {"headers": [{"name": "name"},
   {"name": "type"},
   {"name": "null"},
   {"name": "key"},
   {"name": "computed column"},
   {"name": "watermark"}],
  "rows": [{"cells": [{"value": "id"},
     {"value": "INT"},
     {"value": "true"},
     {"value": ""},
     {"value": ""},
     {"value": ""}]}]}}"""

        json_data = json.loads(json_string)
        df = json_convert_to_dataframe(json_data)
        assert df.iloc[0]['name'] == 'id'
        assert df.iloc[0]['type'] == 'INT'
        assert df.iloc[0]['null'] == 'true'

    def test_json_conversion_ignores_results_without_table(self):
        json_string = """{"result": "RESULT_NO_TABLE"}"""

        json_data = json.loads(json_string)
        result = json_convert_to_dataframe(json_data)
        print(result)
        assert result == json_data
