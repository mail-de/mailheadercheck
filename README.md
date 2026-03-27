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

### enabled (per check)

Each check can be individually disabled by setting `enabled: 0` under
`checks.<check_name>`. A disabled check is skipped entirely: it does not
log, does not count as a violation, and does not appear in the summary
line. This is different from `dry_run: 1`, which still runs the check and
logs the result but does not reject the message.

Example — disable the "not exactly one address in From" check:

```yaml
checks:
  not_exactly_one_address_in_from_header:
    enabled: 0
```

If `enabled` is absent (the default), the check runs normally.

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

### Log output

One summary line is written per message (at INFO level). Examples for
both formats — first an accepted message, then a rejected one:

**plain** (`log_format: plain`):
```
mailheadercheck[1234]: connection_id=A1B2C3D4E5F6 queue_id=3xHt2f001234 client_ip="192.0.2.10" sasl_username="" envelope_from="<sender@example.com>" header_from="Sender Name <sender@example.com>" header_subject="Hello world" header_date="Wed, 23 Jun 2021 16:30:55 +0200" error_response_text="" result=accept actiontaken=accept dry_run=no
mailheadercheck[1234]: connection_id=A1B2C3D4E5F6 queue_id=3xHt2f001235 client_ip="192.0.2.10" sasl_username="" envelope_from="<sender@example.com>" header_from="missing-from-header" header_subject="Hello world" header_date="Wed, 23 Jun 2021 16:30:55 +0200" error_response_text="Missing From:-Header" result=reject actiontaken=reject dry_run=no
```

**json** (`log_format: json`):
```json
{"connection_id": "A1B2C3D4E5F6", "queue_id": "3xHt2f001234", "client_ip": "192.0.2.10", "sasl_username": null, "envelope_from": "<sender@example.com>", "header_from": "Sender Name <sender@example.com>", "header_subject": "Hello world", "header_date": "Wed, 23 Jun 2021 16:30:55 +0200", "error_response_text": "", "result": "accept", "actiontaken": "accept", "dry_run": "no"}
{"connection_id": "A1B2C3D4E5F6", "queue_id": "3xHt2f001235", "client_ip": "192.0.2.10", "sasl_username": null, "envelope_from": "<sender@example.com>", "header_from": "missing-from-header", "header_subject": "Hello world", "header_date": "Wed, 23 Jun 2021 16:30:55 +0200", "error_response_text": "Missing From:-Header", "result": "reject", "actiontaken": "reject", "dry_run": "no"}
```

Field notes:

* `connection_id` — random 12-character ID assigned per TCP connection;
  links debug log lines to the summary line for that connection.
* `queue_id` — Postfix queue ID.
* `sasl_username` — authenticated SASL username, or `null` / empty if the
  connection is not authenticated.
* `error_response_text` — name of the failing check, or empty if the
  message was accepted. In dry_run mode, multiple violations are listed
  comma-separated.
* `result` — `accept` or `reject` based on what the checks found.
* `actiontaken` — `accept` or `reject` reflecting what was actually done.
  Differs from `result` when dry_run is active: `result` can be `reject`
  while `actiontaken` is `accept`.
* `header_from` and `header_subject` — set to `privacy-mode-active` when
  `log_privacy_mode: 1`. Set to `missing-from-header` /
  `missing-subject-header` or `multiple-from-headers` /
  `multiple-subject-headers` in the respective error cases.

### socket

The "socket" setting can have one of the following formats:

* inet:port@ipv4
* inet6:port@ipv6
* unix:/path/to/socket
* local:/path/to/socket

### add_result_header

Setting "add_result_header" to 1 will add a header to the email with
the name "X-MailHeaderCheck". It contains a JSON string with the fields
"connection_id", "queue_id", "error_response_text", "result",
"actiontaken" and "dry_run".

### The checks: section

**All checks are always active by default.** Listing or omitting a check
name in the `checks:` section does not enable or disable it — the section
only configures per-check options. To fully disable a single check, set
`enabled: 0` for it (see [enabled (per check)](#enabled-per-check) above).

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

If you have installed *miltertest*, you can run the tests from the
tests/ folder by simply calling the testing.sh script on a shell.

```
sudo apt install -V miltertest   # if it doesn't exist, maybe it's part of opendkim-tools
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
   * build a minimal image with the milter. While building, it will also run
     the tests.
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
