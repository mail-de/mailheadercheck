# About

*mailheadercheck* is a Postfix milter.

It checks some headers for RFC/BCP validity.

Based on the milter "verifyemail" of Christian Rößner:
<https://gitlab.roessner-net.de/croessner/verifyemail/>

## Features

The current implementation does the following checks:

* No From:-header will result in a reject (reason: RFC violation)
* More than one From:-header will result in a reject (reason: RFC violation)
* An empty From:-header will result in a reject (reason: RFC violation)
* Not exactly one e-mail address is listed in the From:-header. This is a
    limitation and will probably change in the future by adding a header.
    Currently this results in a reject.
* More than one Subject:-header will result in a reject (reason: RFC violation)
* A Subject:-header which is too long will result in a reject
* No Date:-header will result in a reject (reason: RFC violation)
* More than one Date:-header will result in a reject (reason: RFC violation)
* An empty Date:-header will result in a reject (reason: RFC violation)
* An invalid Date:-header will result in a reject (reason: RFC violation)
* More than one Sender:-header will result in a reject (reason: RFC violation)
* More than one Reply-To:-header will result in a reject (reason: RFC violation)
* More than one To:-header will result in a reject (reason: RFC violation)
* More than one Cc:-header will result in a reject (reason: RFC violation)
* No Message-ID:-header will result in a reject (reason: BCP violation)
* More than one Message-ID:-header will result in a reject (reason: RFC violation)
* More than one In-Reply-To:-header will result in a reject (reason: RFC violation)
* More than one References:-header will result in a reject (reason: RFC violation)

## Installation

Install libmilter and the python bindings (often known as pymilter). Place the
mailheadercheck script into /usr/local/sbin/. Place the systemd unit file into
/etc/systemd/system/:

```
sudo apt install python3-dev libmilter-dev python3-pip python3-yaml
sudo pip3 install pymilter
sudo cp mailheadercheck /usr/local/sbin/
sudo cp -r mailheaderchecklib /usr/local/sbin/
sudo chmod 755 /usr/local/sbin/mailheadercheck
sudo cp contrib/systemd/mailheadercheck.service /etc/systemd/system/
sudo mkdir /etc/mailheadercheck
sudo cp examples/config.yaml /etc/mailheadercheck
mailheadercheck --help
```

## Configuration file

The YAML configuration file will be read from the following locations:

* a path given by the --config parameter
* /etc/mailheadercheck/config.yaml
* ./config.yaml

If there is no config file found, the program exits.

## Configuration options

**Please edit your config.yaml according to your needs (see examples/config.yaml).**

### debug

debug=0 (default) only outputs the "summary line" at the end with the results.

debug=1 additionally outputs some log lines for each check that is run.

### dry_run

The milter has a dry-run mode which can be activated by
globally setting "dry_run" to "1" in the config file.

If there is no setting found in the config.yaml, dry-run is active by default.

Additionally, you can change the "dry_run" setting in each check
individually. With this you can either set "dry_run" globally to 1, and
then individual checks to 0. Or the other way around.

### log_target

You can choose from the following log targets:

* syslog (also set "syslog_name" and "syslog_facility" then)
* stdout (for Docker)
* file (also set "log_filepath" then)

### log_format

This can be set to either "plain" or "json". This only affects the
"summary line" when debug=0. It does not affect the DEBUG log lines
which are written when debug=1.

### log_privacy_mode

log_privacy_mode=1 (default) activates the privacy mode, which does not
write the Subject:-header or From:-header to the logfile.

log_privacy_mode=0 deactivates the privacy mode.

### socket

The "socket" setting can have one of the following formats:

* inet:port@ipv4
* inet6:port@ipv6
* unix:/path/to/socket

### add_result_header

Setting "add_result_header" to 1 will add a header to the email with
the name "X-MailHeaderCheck". It contains a JSON string with the "qid",
"error_response_text", "result", "actiontaken" and "dry_run".

### Exclusion options (per check)

Each check can be configured with exclusion lists to skip enforcement for
specific senders.
All comparisons are case-insensitive. Configure these under
`checks.<check_name>`:

* `exclude_fromheader_domains`: list of domains to skip when a From:
  header address matches the domain.
* `exclude_fromheader_addresses`: list of full email addresses from the
  From: header to skip.
* `exclude_envelopefrom_domains`: list of domains to skip when the SMTP
  MAIL FROM address matches the domain.
* `exclude_envelopefrom_addresses`: list of full SMTP MAIL FROM addresses
  to skip (angle brackets are ignored).
* `exclude_ips`: list of IPs or CIDR networks to skip, matching the
  client IP.
* `exclude_sasl_usernames`: list of authenticated SASL usernames to skip
  (useful on submission servers).

Example:

```yaml
checks:
  missing_messageid_header:
    exclude_fromheader_domains:
      - domain_sending_no_msgid.example.com
    exclude_envelopefrom_domains:
      - domain_sending_no_msgid.example.com
    exclude_ips:
      - 127.0.0.1
      - 12.34.56.0/24
    exclude_sasl_usernames:
      - alice
      - bob
    exclude_fromheader_addresses:
      - user@example.org
    exclude_envelopefrom_addresses:
      - bounce@example.org
```

## Start the systemd service

Reload the mailheadercheck.service file and start the systemd service:

```
sudo systemctl daemon-reload
sudo systemctl enable mailheadercheck
sudo systemctl start mailheadercheck
```

## Configure the milter in Postfix

Add the milter in Postfix to the smtpd_milters setting in the main.cf:

```
smtpd_milters = ..., inet:127.0.0.1:30073, ...
```

## Testing

If you have installed *miltertest* from the OpenDKIM project, you can run the
tests from the tests/ folder by simply calling the testing.sh script on a shell.

```
sudo apt install -V opendkim-tools
chmod 700 mailheadercheck
chmod 700 testing.sh
./testing.sh
# or run a single test:
miltertest -s tests/test-01.lua
```

Enjoy

## Run with Docker Compose

This repository includes everything to run the milter via Docker. The
Dockerfile and docker-compose.yml live at the project root.

Quickstart:

1) Build and start

```sh
docker compose up -d --build
```

   This will:
   * build a minimal Python image with the milter
   * mount docker/config.yaml into the container at /config/config.yaml
   * listen on TCP port 30073 inside the container and publish it to the host

2) Configure Postfix to use the milter

   Add to main.cf (replace 127.0.0.1 with the appropriate host/IP where
   the container runs if needed):

```conf
smtpd_milters = ..., inet:127.0.0.1:30073, ...
```

3) Logs

   The default container config (docker/config.yaml) logs to stdout. You
   can view logs with:

```sh
docker compose logs -f
```

4) Healthcheck

   The compose file includes a healthcheck that verifies the TCP listener.

Notes

* Config file location: By default the container expects /config/config.yaml;
  docker-compose mounts docker/config.yaml there. Adjust to your environment
  as needed.
* Socket type: For Docker, using a TCP socket is simplest. If you prefer a
  UNIX domain socket, mount a volume and set socket: unix:/path/to/socket in
  the config, then point Postfix to that path inside the same mount namespace.
* Non-root: The container runs as a non-root user and exposes port 30073
  (non-privileged).

### Validate configuration (optional)

You can validate the configuration without starting the milter:

```sh
docker compose run --rm mailheadercheck --config /config/config.yaml --configcheck
```
