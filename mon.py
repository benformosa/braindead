#!/usr/bin/python3

# TODO:
# - proxy
# - settings file or commandline

from timeit import default_timer as timer
from urllib.parse import urlparse
import argparse
import http.client
import socket
import yaml

v_print = lambda *a: None  # do-nothing function
services = {}
timeout = 60

# From https://stackoverflow.com/a/1140822
def get_status_code(scheme, host, path="/"):
    """ This function retreives the status code of a website by requesting
        HEAD data from the host. This means that it only requests the headers.
        If the host cannot be reached or something else goes wrong, it returns
        None instead.
    """
    if scheme == 'http':
        http_client_connection = http.client.HTTPConnection
    elif scheme == 'https':
        http_client_connection = http.client.HTTPSConnection
    else:
        raise ValueError("Unknown scheme {}".format(scheme))

    try:
        conn = http_client_connection(host, timeout=timeout)
        conn.request("HEAD", path)
        return conn.getresponse().status
    except socket.timeout as e:
        v_print(1, e)
        return 'Socket Timeout'
    except http.client.HTTPException as e:
        v_print(1, e)
        return None

def check_service(service, print_output=False):
    """ Given a dict defining a service, check the service's status and update the
    dict.
    """
    v_print(3, "Starting service {}".format(service['name']))

    # Parse URL
    u = urlparse(service['url'])

    # Set default expected status code to 200
    if 'expect_code' not in service:
        service['expect_code'] = 200

    v_print(3, "    connecting to url {}://{}{}".format(
        u.scheme, u.netloc, u.path))

    # Get status code and response time
    start = timer()
    service['status'] = get_status_code(u.scheme, u.netloc, (u.path or "/"))
    service['response_time'] = timer() - start

    v_print(2, "Service: {} - Status: {} - Time: {}".format(
        service['name'], service['status'], service['response_time']))

    # Set ok based on expected status code
    service['ok'] = 'NO'
    if service['expect_code'] == service['status']:
        service['ok'] = 'OK'

    if print_output:
        print("{} - {}".format(service['name'], service['ok']))

def check_services(services, print_output=False):
    """Check status for an array of dicts.
    """
    for service in services:
        check_service(service, print_output)
    return services

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--services', metavar='FILE', type=str,
            default='services.yml',
            help="Path to YAML file defining services to check")
    parser.add_argument('-w', '--wait', metavar='SECONDS', type=int,
            default=10, help="Seconds to wait before timeout.")
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
 
    # Open services file. Expects an array of dicts.
    with open(args.services, 'r') as stream:
        try:
            services = yaml.load(stream)
        except yaml.YAMLError as e:
            print(e)

    check_services(services, print_output=True)

if __name__ == '__main__':
    main()
