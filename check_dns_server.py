#!/usr/bin/env python

"""
This is a simple Nagios plugin to query a DNS server.

Returns OK if the server replies.
"""

__author__ = 'jcrsilva'
__license__ = 'The Unlicense'
__version__ = '1.0.0'

import argparse

from dns.exception import Timeout
from dns.resolver import NXDOMAIN, Resolver

import nagiosplugin


class CheckDNS(nagiosplugin.Resource):
    """CheckDNS class."""

    __dns_resolver = None

    @property
    def _dns_resolver(self):
        if not self.__dns_resolver:
            self.__dns_resolver = Resolver()

            self.__dns_resolver.nameservers = [self.args.hostname]
            self.__dns_resolver.port = self.args.port
            self.__dns_resolver.timeout = self.args.timeout
            self.__dns_resolver.lifetime = self.args.timeout

        return self.__dns_resolver

    def __init__(self, args):
        """
        Class constructor.

        :param args: command line arguments
        """
        self.args = args

    def probe(self):
        """
        Nagios probe method.

        :return: Metrics
        """
        try:
            answer = self._dns_resolver.query(self.args.query)
            return [
                nagiosplugin.Metric(
                    name=str(answer.rrset),
                    value=True,
                    context='dns'
                )
            ]
        except Timeout as e:
            return [
                nagiosplugin.Metric(
                    name=e.message,
                    value=False,
                    context='dns'
                )
            ]
        except NXDOMAIN as e:
            return [
                nagiosplugin.Metric(
                    name=e.message,
                    value=False,
                    context='dns'
                )
            ]
        except Exception as e:
            raise nagiosplugin.CheckError(e.message)


class CheckDNSContext(nagiosplugin.Context):
    """CheckDNS context for nagiosplugin."""

    def __init__(self):
        """Constructor."""
        super(self.__class__, self).__init__('dns')

    def evaluate(self, metric, resource):
        """
        Evaluate metric result.

        :param metric: Metric
        :param resource: Resource
        :return: Metric state
        """
        if metric.value:
            return self.result_cls(nagiosplugin.state.Ok, metric=metric)
        else:
            return self.result_cls(nagiosplugin.state.Critical, metric=metric)

    def describe(self, metric):
        """
        Describe the metric.

        :param metric: Metric
        :return: Metric description
        """
        return metric.name


def get_args():
    """
    Grab args from CLI.

    :return: Argument dict
    """
    argp = argparse.ArgumentParser(
        description=__doc__
    )

    argp.add_argument('-H', '--hostname', action='store', required=True,
                      help='Hostname/IP of the server to query'
                      )
    argp.add_argument('-P', '--port', action='store', required=False,
                      default=53, type=int,
                      help='Port to check DNS service on, default: 53'
                      )
    argp.add_argument('-Q', '--query', action='store', required=False,
                      default='example.com',
                      help='Domain to query, default: example.com - If NXDOMAIN critical'
                      )
    argp.add_argument('-T', '--timeout', action='store', required=False,
                      default=5, type=int,
                      help='Timeout for DNS query'
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
        CheckDNS(args),
        CheckDNSContext(),
    ).main()


if __name__ == '__main__':
    main()
