# Braindead Monitoring
A simple tool to monitor if a service, mostly a web site, is up.

## Project goals

* Check the status of URLs without a full-blown monitoring solution.
* Quick to get started:
  * Simple YAML configuration.
  * Run on commandline and web with the same config files.

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
