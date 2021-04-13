# if VVP_LOCAL_RUNNING has any value (even false/0) then all tests will run
import os
import string
import unittest
import random
from uuid import UUID

from IPython.testing.globalipapp import get_ipython

from jupytervvp import VvpMagics
from jupytervvp.vvpsession import VvpSession

SKIP_INTEGRATION_TESTS = os.environ.get('SKIP_INTEGRATION_TESTS', False)


def random_string():
    return ''.join(random.choices(string.digits + "abcdef", k=4))


@unittest.skipIf(SKIP_INTEGRATION_TESTS, 'Requires locally running VVP backend.')
class VvpMagicsTestsAgainstBackend(unittest.TestCase):
    ipython_session = None

    @classmethod
    def setUpClass(cls):
        cls.ipython_session = get_ipython()

    def setUp(self):
        self.ipython_session.run_cell(raw_cell='%reset -f')
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    def test_flink_sql_executes_show_tables(self):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -p 8280 -s session1"
        magics.connect_vvp(connect_magic_line)

        sql_magic_line = ""
        sql_magic_cell = "SHOW TABLES"

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert "table name" in response.columns

    def test_flink_sql_executes_create_table(self):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -p 8280 -s session1"
        magics.connect_vvp(connect_magic_line)

        table_name = "testTable{}".format(random_string())

        sql_magic_line = ""
        sql_magic_cell = """CREATE TABLE `{}` (id int)
COMMENT 'SomeComment'
WITH (
'connector.type' = 'kafka',
'connector.version' = 'universal',
'connector.topic' = 'testTopic',
'connector.properties.bootstrap.servers' = 'localhost',
'connector.properties.group.id' = 'testGroup',
'connector.startup-mode' = 'earliest-offset'
)""".format(table_name)

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert response['result'] == 'RESULT_SUCCESS'

    def test_flink_sql_executes_insert(self):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -p 8280 -s session1"
        magics.connect_vvp(connect_magic_line)

        table_names = ["testTable{}{}".format(i, random_string()) for i in [1, 2]]

        sql_ddl_magic_line = ""
        sql_ddl_magic_cells = ["""CREATE TABLE `{}` (id int)
COMMENT 'SomeComment'
WITH (
    'connector.type' = 'kafka',
    'connector.version' = 'universal',
    'connector.topic' = 'myTopic',
    'connector.properties.bootstrap.servers' = 'localhost',
    'format.type' = 'json',
    'format.derive-schema' = 'true'
)""".format(table_name) for table_name in table_names]

        for cell in sql_ddl_magic_cells:
            response = magics.flink_sql(sql_ddl_magic_line, cell)
            assert response['result'] == 'RESULT_SUCCESS'

        sql_dml_magic_line = ""
        sql_magic_dml_cell = """INSERT INTO {} SELECT * FROM {}""".format(table_names[0], table_names[1])

        response = magics.flink_sql(sql_dml_magic_line, sql_magic_dml_cell)
        assert UUID(response, version=4)


if __name__ == '__main__':
    unittest.main()
