#!/usr/bin/env python

import argparse

import dns
from dns.resolver import NXDOMAIN
from dns.exception import Timeout
import nagiosplugin
from nagiosplugin.state import Ok, Critical

__doc__ = """
This is a simple Nagios plugin to query a DNS server

Returns OK if the server replies.
"""

__author__ = 'jcrsilva'
__license__ = 'The Unlicense'
__version__ = '1.0.0'


class CheckDNS(nagiosplugin.Resource):
    _dns_resolver = None

    @property
    def dns_resolver(self):
        if not self._dns_resolver:
            self._dns_resolver = dns.resolver.Resolver()

            self._dns_resolver.nameservers = [self.args.hostname]
            self._dns_resolver.port = self.args.port
            self._dns_resolver.timeout = self.args.timeout
            self._dns_resolver.lifetime = self.args.timeout

        return self._dns_resolver

    def __init__(self, args):
        self.args = args

    def probe(self):
        try:
            answer = self.dns_resolver.query(self.args.query)
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
    def __init__(self):
        super(self.__class__, self).__init__('dns')

    def evaluate(self, metric, resource):
        if metric.value:
            return self.result_cls(Ok, metric=metric)
        else:
            return self.result_cls(Critical, metric=metric)

    def describe(self, metric):
        return metric.name


def get_args():
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
    args = get_args()
    nagiosplugin.Check(
        CheckDNS(args),
        CheckDNSContext(),
    ).main()

if __name__ == '__main__':
    main()
