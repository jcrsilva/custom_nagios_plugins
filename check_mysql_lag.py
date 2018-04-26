#!/usr/bin/env python

import argparse

import pymysql
import nagiosplugin

"""
This is a simple python script to check the replica lag in a MySQL instance.
If the instance is a Master, it just returns OK.

(if you're the master then, logically, you're 0 seconds behind yourself)

It uses the nagiosplugin framework to reduce boilerplate code and make outputting
perfdata easier.
It uses pymysql, a pure python implementation of a mysql driver.
"""

__author__ = 'jcrsilva'
__license__ = 'The Unlicense'
__version__ = '1.0.0'


class CheckMySQLLag(nagiosplugin.Resource):
    _mysql_connection = None

    @property
    def mysql_connection(self):
        if not self._mysql_connection:
            self._mysql_connection = pymysql.connect(
                host=self.args.hostname,
                user=self.args.username,
                password=self.args.password,
                autocommit=True,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor,
            )

        return self._mysql_connection

    def query(self, sql):
        with self.mysql_connection.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()[0]

    def __init__(self, args):
        super(self.__class__, self).__init__()
        self.args = args

    def probe(self):
        sql = """
        SELECT 
        CASE 
            WHEN @@global.read_only = 0 THEN true
            ELSE false
        END AS is_master;
        """
        result = self.query(sql)
        if result['is_master'] == 1:
            return nagiosplugin.Metric('master',
                                       True,
                                       context='master')
        else:
            result = self.query('SHOW SLAVE STATUS').get('Seconds_Behind_Master', 0)
            return nagiosplugin.Metric('lag',
                                       value=result,
                                       uom='s',
                                       context='lag')


def get_args():
    argp = argparse.ArgumentParser(
        description="Checks the replica lag of a MySQL Slave or returns OK if it's a Master"
    )

    argp.add_argument('-H', '--hostname', action='store', required=False, default='localhost',
                      help='Hostname of the MySQL DB, default: localhost'
                      )
    argp.add_argument('-P', '--port', action='store', required=False,
                      default=3306, type=int,
                      help='Port of the MySQL DB, default: 3306'
                      )

    argp.add_argument('-U', '--username', action='store', required=False)
    argp.add_argument('-p', '--password', action='store', required=False, default='')

    argp.add_argument('-w', '--warning', action='store', required=True,
                      type=int,
                      help='WARNING threshold for lag value in seconds'
                      )
    argp.add_argument('-c', '--critical', action='store', required=True,
                      type=int,
                      help='CRITICAL threshold for lag value in seconds'
                      )

    return argp.parse_args()


@nagiosplugin.guarded
def main():
    args = get_args()
    nagiosplugin.Check(
        CheckMySQLLag(args),
        nagiosplugin.ScalarContext('lag', args.warning, args.critical),
        nagiosplugin.Context(name='master', fmt_metric='Is master')
    ).main()

if __name__ == '__main__':
    main()
