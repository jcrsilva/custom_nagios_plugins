#!/usr/bin/env python

"""
This Nagios plugin checks the state of a zookeeper cluster via the "4 letter words".

Its main purpose is to check a Zookeeper status for OK nodes and check if more than one
believes he is a leader.
"""

from __future__ import division


__author__ = 'jcrsilva'
__license__ = 'The Unlicense'
__version__ = '1.0.0'

import argparse
import re
import socket
import sys
from telnetlib import Telnet

import nagiosplugin

# Regex to validate a zookeeper connection string
ZK_CONNECTION_STRING_RE = '^([a-zA-Z0-9.]+(:[0-9]+)?)(,[a-zA-Z0-9.]+(:[0-9]+)?)*$'

# Timeout when attempting to connect to remote zk server
ZK_TIMEOUT = 5


class CheckZK(nagiosplugin.Resource):
    """CheckZK class."""

    def __init__(self, hosts):
        """
        Class constructor.

        :param hosts: command line arguments
        """
        self.hosts = hosts

    @staticmethod
    def _zk_tn(host_tpl, data):
        try:
            tn = Telnet(host=host_tpl[0], port=host_tpl[1], timeout=ZK_TIMEOUT)
            tn.write(data)
            ret = tn.read_all()
            tn.close()
            return ret
        except socket.error:
            return None

    def probe(self):
        """
        Nagios probe method.

        :return: Metrics
        """
        def probe_ok(host):
            return CheckZK._zk_tn(host, 'ruok') == 'imok'

        def probe_leader(host):
            return re.search("Mode: ([a-z]+)", CheckZK._zk_tn(host, 'stat')).group(1) == 'leader'

        status = {}
        for host in self.hosts:
            status[host] = {
                "ok": probe_ok(host)
            }
            if status[host]["ok"]:
                status[host]["leader"] = probe_leader(host)

        return [
            nagiosplugin.Metric("ruok", status),
            nagiosplugin.Metric("leader", status)
            ]


class CheckZKLeaderContext(nagiosplugin.Context):
    """Context to evaluate leaders."""

    def __init__(self):
        """Constructor."""
        super(self.__class__, self).__init__('leader')

    def evaluate(self, metric, resource):
        """
        Evaluate metric result.

        :param metric: Metric
        :param resource: Resource
        :return: Metric state
        """
        leaders = [node for node in metric.value if metric.value[node].get("leader")]

        if len(leaders) <= 0:
            return self.result_cls(nagiosplugin.state.Critical, "Cluster has no leader", metric=metric)
        elif len(leaders) == 1:
            return self.result_cls(nagiosplugin.state.Ok, metric=metric)
        else:
            return self.result_cls(nagiosplugin.state.Critical, "More than one leader detected!", metric=metric)

    def describe(self, metric):
        """
        Describe metric.

        :param metric: Metric
        :return: Metric description
        """
        return "{} are both leaders".format(
            ",".join([":".join(node) for node in metric.value if metric.value[node].get("leader")])
        )


class CheckZKOKContext(nagiosplugin.Context):
    """Context to evaluate if nodes are OK."""

    def __init__(self):
        """Constructor."""
        super(self.__class__, self).__init__('ruok')

    def evaluate(self, metric, resource):
        """
        Evaluate metric result.

        :param metric: Metric
        :param resource: Resource
        :return: Metric state
        """
        has_quorum_number = int(round(len(metric.value) / 2))
        up_nodes = len([node for node in metric.value.values() if node.get("ok")])

        if up_nodes >= len(metric.value):
            return self.result_cls(nagiosplugin.state.Ok, metric=metric)
        elif up_nodes >= has_quorum_number:
            return self.result_cls(nagiosplugin.state.Warn, "Cluster has nodes down but has quorum", metric=metric)
        else:
            return self.result_cls(nagiosplugin.state.Critical, "Cluster does not have quorum", metric=metric)

    def describe(self, metric):
        """
        Describe metric.

        :param metric: Metric
        :return: Metric description
        """
        return "{}/{} nodes are OK".format(
            len([node for node in metric.value.values() if node.get("ok")]), len(metric.value)
        )

    def performance(self, metric, resource):
        """
        Format performance data.

        :param metric: Metric
        :param resource: Resource
        :return: Performance
        """
        # for dev mode
        if len(metric.value) == 1:
            crit = nagiosplugin.Range("~:0".format(int(round(len(metric.value) / 2))))
            warn = None

        # for 3 node cluster
        elif 1 < len(metric.value) < 4:
            crit = nagiosplugin.Range("~:2".format(int(round(len(metric.value) / 2))))
            warn = None

        # anything bigger
        if len(metric.value) >= 4:
            crit = nagiosplugin.Range("~:{}".format(int(round(len(metric.value) / 2))))
            warn = nagiosplugin.Range("{}:{}".format(int(round(len(metric.value) / 2))+1, len(metric.value)-1))

        return nagiosplugin.Performance(
            label="OK ZK nodes",
            value=len(metric.value),
            uom="Number",
            warn=warn,
            crit=crit,
        )


def get_args():
    """
    Grab args from CLI.

    :return: Argument dict
    """
    argp = argparse.ArgumentParser(
        description=__doc__
    )

    argp.add_argument('-S', '--connection', action='store', required=True,
                      help='Zookeeper connection string'
                      )

    return argp.parse_args()


@nagiosplugin.guarded
def main():
    """
    Main.

    :return:
    """
    args = get_args()

    # Validate connection string
    if not re.match(ZK_CONNECTION_STRING_RE, args.connection):
        print "Zookeeper connection string is not valid"
        sys.exit(2)

    hosts = []
    for host in args.connection.split(','):
        if ':' in host:
            hosts.append(tuple(host.split(':')))
        else:
            hosts.append((host, 2181))

    nagiosplugin.Check(
        CheckZK(hosts),
        CheckZKOKContext(),
        CheckZKLeaderContext(),
    ).main()


if __name__ == '__main__':
    main()
