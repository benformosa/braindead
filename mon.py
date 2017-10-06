#!/usr/bin/python3

from timeit import default_timer as timer
from urllib.parse import urlparse
import argparse
import csv
import http.client
import json
import socket
import sys
import threading
import yaml

DEFAULTS = {
    'http': {
        'expect_code': 200,
        'port': 80,
        'path': '/',
    },
    'https': {
        'expect_code': 200,
        'port': 443,
        'path': '/',
    },
    'tcp': {
        'expect_code': 1,
        'port': None,
    }
}

services = []
timeout = 10
v_print = lambda *a: None  # do-nothing function


def get_status_code(service):
    """ Select a function to use to check status, based on scheme.
    """
    if service['scheme'] in ['http', 'https']:
        v_print(3, "      HTTP(S) scheme")
        return get_http_status_code(
            service['scheme'],
            service['host'],
            service['port'],
            service['path']
            )
    elif service['scheme'] == 'tcp':
        return get_tcp_status(service['host'], service['port'])
    else:
        raise ValueError("Unknown scheme {}".format(scheme))

def get_http_status_code(scheme, host, port, path="/"):
    """ This function retreives the status code of a website by requesting
        HEAD data from the host. This means that it only requests the headers.
        None instead.
        Adapted from https://stackoverflow.com/a/1140822
    """
    if scheme == 'http':
        http_client_connection = http.client.HTTPConnection
    elif scheme == 'https':
        http_client_connection = http.client.HTTPSConnection

    v_print(3, "        Attempting {} connection to host {}".format(scheme, host))

    try:
        conn = http_client_connection(host, port, timeout=timeout)
        conn.request("HEAD", path)
        return conn.getresponse().status
    except socket.timeout as e:
        v_print(1, e)
        return 'Socket Timeout'
    except http.client.HTTPException as e:
        v_print(1, e)
        return None

def get_tcp_status(host, port):
    """ Check if a host is listening on a TCP port.
        Returns 1 for success, and None for failure.
    """
    v_print(3, "        Attempting tcp connection to host {}, port {}".format(host, port))

    try:
        c = socket.create_connection((host, port), timeout)
        v_print(3, "        Connection to " + host + " " + port + " port (tcp) succeeded!")
        return 1
        c.close()
    except socket.error as m:
        v_print(3, "        Connection to " + host + " " + port + " port (tcp) failed. ")
        return None

def validate_services(services):
    """ Update an array of dicts with canonical values for all fields.
    """
    for service in services:
        u = urlparse(service['url'])

        # Set the scheme and check that it's supported
        service['scheme'] = u.scheme
        if service['scheme'] not in DEFAULTS:
            raise RuntimeError("Service '{}' - Specified scheme '{}' is not supported".format(
                service['Name'], service['scheme']
            ))

        # Set default expected status code to 200
        if 'expect_code' not in service:
            service['expect_code'] = DEFAULTS[u.scheme]['expect_code']

        # Set host and port
        if ':' in u.netloc:
            (service['host'], service['port']) = u.netloc.split(':')
        else:
            service['host'] = u.netloc
            service['port'] = DEFAULTS[u.scheme]['port']

        if service['port'] == None:
            raise RuntimeError("Service '{}' - No port specified".format(service['name']))

        # Set scheme-specific stuff
        if service['scheme'] in ['http', 'https']:
            service['path'] = DEFAULTS[u.scheme]['path']

    return services

def check_service(service):
    """ Given a dict defining a service, check the service's status and update the
    dict.
    """
    v_print(3, "Starting service {}".format(service['name']))

    # Parse URL
    u = urlparse(service['url'])

    v_print(3, "    connecting to url {}://{}{}".format(
        u.scheme, u.netloc, u.path))

    # Get status code and response time
    start = timer()
    service['status'] = get_status_code(service)
    service['response_time'] = timer() - start

    v_print(2, "Service: {} - Status: {} - Time: {}".format(
        service['name'], service['status'], service['response_time']))

    # Set ok based on expected status code
    service['ok'] = 'NO'
    if service['expect_code'] == service['status']:
        service['ok'] = 'OK'

    v_print(1, "{} - {}".format(service['name'], service['ok']))

def check_services_threaded(services):
    """ Check status for an array of dicts.
    """

    services = validate_services(services)

    threads = []
    for service in services:
        # Create and start a thread for each service
        v_print(3, "Creating thread 'Check service {}'".format(service['name']))
        t = threading.Thread(
                name="Check service {}".format(service['name']),
                target=check_service,
                args=(service,)
            )
        t.start()
        threads.append(t)

    # Wait for each service check to complete
    for t in threads:
        v_print(3, "Joining thread 'Check service {}'".format(service['name']))
        t.join()

    return services

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--services', metavar='FILE', type=str,
            default='services.yml',
            help="Path to YAML file defining services to check")
    parser.add_argument('-w', '--wait', metavar='SECONDS', type=int,
            default=10, help="Seconds to wait before timeout")
    parser.add_argument('-o', '--output', metavar='FORMAT', type=str,
            choices=['plain', 'yaml', 'json', 'csv'],
            default='plain',
            help="Output format")
    parser.add_argument('-v', '--verbosity', action="count",
            help="increase output verbosity (e.g., -vv is more than -v)")
    args = parser.parse_args()

    # Set up v_print function for verbose output
    if args.verbosity:
        def _v_print(*verb_args):
            if verb_args[0] > (3 - args.verbosity):
                print(verb_args[1])
    else:
        _v_print = lambda *a: None  # do-nothing function

    global v_print
    v_print = _v_print

    v_print(3, "Opening services file {}".format(args.services))
    # Open services file. Expects an array of dicts.
    with open(args.services, 'r') as stream:
        try:
            services = yaml.load(stream)
        except yaml.YAMLError as e:
            print(e)

    v_print(3, "Checking services")
    check_services_threaded(services)

    if args.output == 'plain':
        template = "{}\t\t{}\t{}\t{}"
        print(template.format('Name', 'OK', 'Status', 'Response (sec)'))
        for service in services:
            print(
                template.format(
                    service['name'],
                    service['ok'],
                    service['status'],
                    service['response_time']
                )
            )
    elif args.output == 'csv':
        fields = ['name', 'ok', 'status', 'response_time', 'url', 'expect_code']
        writer = csv.DictWriter(sys.stdout, fields, dialect='excel')
        writer.writeheader()

        for service in services:
            writer.writerow(service)
    elif args.output == 'yaml':
        print(yaml.dump(services, default_flow_style=False))
    elif args.output == 'json':
        print(json.dumps(services, sort_keys=True, indent=2))

if __name__ == '__main__':
    main()
