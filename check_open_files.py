#!/usr/bin/env python

"""h
This is a simple python script to ceck the number of open files by process in a linux system.

It uses the nagiosplugin framework to reduce boilerplate code and make outputting
perfdata easier.
No external libs except for that.
"""
from __future__ import division

__author__ = 'jcrsilva'
__license__ = 'The Unlicense'
__version__ = '1.0.0'

import argparse
import re
import os
from collections import defaultdict
from sys import maxint

import nagiosplugin


class CheckOpenFiles(nagiosplugin.Resource):
    """CheckOpenFiles class."""

    def __init__(self, args):
        """
        Constructor.

        :param args: CLI arguments.
        """
        super(self.__class__, self).__init__()
        self.args = args

    def probe(self):
        """
        Probe method.

        :return:
        """

        def get_min_limit_from_table(limits):
            return min(
                map(
                    lambda x: int(x) if str(x) != "unlimited" else maxint,
                    map(
                        lambda x: re.split(r"\s{2,}", x.strip()),
                        filter(
                            lambda x: "open files" in x, limits[1:]
                        )
                    )[0][1:3]
                )
            )

        limits = defaultdict(dict)
        for i in filter(lambda x: x.isdigit(), os.listdir("/proc/")):
            try:
                with open(os.path.join("/proc/", i, "limits"), "r") as f:
                    limits[i]["min_file_limit"] = get_min_limit_from_table(f.readlines())
                with open(os.path.join("/proc/", i, "cmdline"), "r") as f:
                    limits[i]["cmdline"] = "({pid}) {cmd}".format(pid=i, cmd="".join(f.readlines()).split('\x00')[0])
                limits[i]["curr_open_files"] = len(os.listdir(os.path.join("/proc/", i, "fd")))
            except (IOError, OSError):
                # probably the file we were trying to access does not exist anymore
                limits.pop(i)
                continue

            limits[i]["usage_percent"] = int((limits[i]["curr_open_files"] / limits[i]["min_file_limit"]) * 100)

            yield nagiosplugin.Metric(
                name=limits[i]["cmdline"],
                value=limits[i]["usage_percent"],
                uom="percent",
                min=0,
                context="open files",
            )


def get_args():
    """
    Grab CLI arguments.

    :return: CLI arguments dict.
    """
    argp = argparse.ArgumentParser(
        description="Checks the number of open files for processes in system."
    )

    argp.add_argument('-w', '--warning', action='store', required=True,
                      type=int,
                      help='WARNING threshold for number of open files in percentage'
                      )
    argp.add_argument('-c', '--critical', action='store', required=True,
                      type=int,
                      help='CRITICAL threshold for number of open files in percentage'
                      )

    return argp.parse_args()


@nagiosplugin.guarded
def main():
    """
    Main.

    :return:
    """

    args = get_args()
    nagiosplugin.Check(
        CheckOpenFiles(args),
        nagiosplugin.ScalarContext('open files', args.warning, args.critical),
    ).main()


if __name__ == '__main__':
    main()
