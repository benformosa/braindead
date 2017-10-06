#!/usr/bin/python3

# TODO:
# - proxy
# - settings file or commandline
# - JSON/YAML output
# - convert to class - begin as constructor

from timeit import default_timer as timer
from urllib.parse import urlparse
import argparse
import http.client
import socket
import threading
import yaml

v_print = lambda *a: None  # do-nothing function
services = []
timeout = 10

def set_timeout(time):
    timeout = time

def get_status_code(scheme, host, path="/"):
    """ Select a function to use to check status, based on scheme.
    """
    if scheme in ['http', 'https']:
        v_print(3, "      HTTP(S) scheme")
        return get_http_status_code(scheme, host, path)
    else:
        raise ValueError("Unknown scheme {}".format(scheme))

def get_http_status_code(scheme, host, path="/"):
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
        conn = http_client_connection(host, timeout=timeout)
        conn.request("HEAD", path)
        return conn.getresponse().status
    except socket.timeout as e:
        v_print(1, e)
        return 'Socket Timeout'
    except http.client.HTTPException as e:
        v_print(1, e)
        return None

def check_service(service):
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

    v_print(1, "{} - {}".format(service['name'], service['ok']))

def check_services(services):
    for service in services:
        check_service(service)
    return services

def check_services_threaded(services):
    """Check status for an array of dicts.
    """
    threads = []
    for service in services:
        v_print(3, "Creating thread 'Check service {}'".format(service['name']))
        t = threading.Thread(
                name="Check service {}".format(service['name']),
                target=check_service,
                args=(service,)
            )
        t.start()
        threads.append(t)

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
 
    v_print(3, "Opening services file {}".format(args.services))
    # Open services file. Expects an array of dicts.
    with open(args.services, 'r') as stream:
        try:
            services = yaml.load(stream)
        except yaml.YAMLError as e:
            print(e)

    v_print(3, "Checking services")
    check_services_threaded(services)

    for service in services:
        print("{} - {}".format(service['name'], service['ok']))

if __name__ == '__main__':
    main()
