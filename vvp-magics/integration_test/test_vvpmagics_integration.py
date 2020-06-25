# if VVP_LOCAL_RUNNING has any value (even false/0) then all tests will run
import os
import string
import unittest
import random

from vvpmagics import VvpMagics
from vvpmagics.vvpsession import VvpSession

has_running_vvp_instance = os.environ.get('VVP_LOCAL_RUNNING', False)


def random_string():
    return ''.join(random.choices(string.digits + "abcdef", k=4))


class VvpMagicsTestsAgainstBackend(unittest.TestCase):

    def setUp(self):
        VvpSession._sessions = {}
        VvpSession.default_session_name = None

    @unittest.skipIf(not has_running_vvp_instance, 'Requires running VVP backend.')
    def test_flink_sql_executes_show_tables(self):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
        magics.connect_vvp(connect_magic_line)

        sql_magic_line = ""
        sql_magic_cell = "SHOW TABLES"

        response = magics.flink_sql(sql_magic_line, sql_magic_cell)
        assert "table name" in response.columns

    @unittest.skipIf(not has_running_vvp_instance, 'Requires running VVP backend.')
    def test_flink_sql_executes_create_table(self):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
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

    @unittest.skipIf(not has_running_vvp_instance, 'Requires running VVP backend.')
    def test_flink_sql_executes_insert(self):
        magics = VvpMagics()
        connect_magic_line = "localhost -n default -s session1"
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
        assert response == "CANCELLED"


if __name__ == '__main__':
    unittest.main()
