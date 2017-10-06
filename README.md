# Braindead Monitoring
A simple tool to monitor if a service, e.g. a web site, is up.

## Project goals

* Check the status of URLs without a full-blown monitoring solution.
* Quick to get started:
  * Simple YAML configuration.
  * Run on commandline and web with the same config files.

## Configuration

### Services

Specify the services you want to monitor as a YAML file. You should define a sequence of mappings with the following keys:

| Key | Description | Mandatory |
|-----|-------------|-----------|
| name | Friendly name of the service | Yes |
| url | URL to the service | Yes |
| expect_code | The expected status code. For HTTP or HTTPS URLs, this should be a HTTP status code. | No |

#### Services Example

```yaml
- name: My Website
  url: https://example.com/healthcheck/
- name: Another website
  url: http://example.net/login/
  expect_code: 401
- name: TCP Service
  url: tcp://portquiz.net:666
```

### Supported schemes

| Scheme | URL Format | Description | Default Port | Default expect_code |
|--------|------------|-------------|--------------|--------------------|
| http | http://host[:port][/path] | Get the HTTP status code of a web page. | 80 | 200 |
| https | https://host[:port][/path] | Get the HTTP status code of a web page. | 443 | 200 |
| tcp | tcp://host:port | Test for listening TCP service. | N/A | 1 |

## Usage

### Command line

```bash
./mon.py -s services.yml
```

### Web

Run the Flask app `web.py` directly, or using an application server.

```bash
./web.py
```

Alternately, use the Docker image to run the web app.

## TODO
* Proxy support using http_proxy and https_proxy environment variables
* Support config file from command line
* Convert to a class
* Add an enable field to services
* Option to only check services file
