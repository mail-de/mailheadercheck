# About

*mailheadercheck* is a Postfix milter.

It checks some headers for RFC validity.

Based on the milter "verifyemail" of Christian Rößner:
 https://gitlab.roessner-net.de/croessner/verifyemail/

## Features

The current implementation does the following checks:

* Zero or more than one From:-header will result in a reject (reason: RFC violation)
* More than one Subject:-header will result in a reject (reason: RFC violation)
* Zero or more than one Date:-header will result in a reject (reason: RFC violation)
* Zero or more than one e-mail address is listed in the From:-header. This is a
  limitation and will probably change in the future by adding a header.
  Currently this results in a reject.
* An empty or invalid Date:-header will result in a reject (reason: RFC violation)
* A Subject:-header which is too long will result in a reject
* More than one Sender:-header will result in a reject (reason: RFC violation)
* More than one Reply-To:-header will result in a reject (reason: RFC violation)
* More than one To:-header will result in a reject (reason: RFC violation)
* More than one Cc:-header will result in a reject (reason: RFC violation)
* More than one Message-ID:-header will result in a reject (reason: RFC violation)
* More than one In-Reply-To:-header will result in a reject (reason: RFC violation)
* More than one References:-header will result in a reject (reason: RFC violation)

## Installation

Install libmilter and the python bindings (often known as pymilter). Place the
mailheadercheck script into /usr/local/sbin/. Place the systemd unit file into
/etc/systemd/system/ and create a user named "milter":

```
sudo apt install libmilter-dev
sudo apt install python3-pip
sudo pip3 install pymilter
sudo cp mailheadercheck /usr/local/sbin/mailheadercheck
sudo chmod 755 /usr/local/sbin/mailheadercheck
sudo cp mailheadercheck.service /etc/systemd/system/
sudo useradd milter -r -s /bin/false
mailheadercheck --help
```

### Configuration of the dry-run

The milter has a dry-run mode which is activated by adding the parameter:
```
--action accept
```
Dry-run is active in the provided mailheadercheck.service file. If you don't
want the dry-run, remove this parameter from the mailheadercheck.service file.

### Configuration of the socket

If you need a different port or IP address, use one of the following parameters:

```
--socket inet:port@ipv4
--socket inet6:port@ipv6
--socket unix:/path/to/socket
```

### Configuration of syslog

You can also change the syslog name and facility or
disable the use of syslog at all. Logs are written to stdout in this case and
`syslog_name` and `syslog_facility` are ignored. This is intended for operation
in docker containers.

```
--syslog_name mailheadercheck
--syslog_facility mail
--syslog_disabled
```

### Start the systemd service

Reload the mailheadercheck.service file and start the systemd service:

```
sudo systemctl daemon-reload
sudo systemctl enable mailheadercheck
sudo systemctl start mailheadercheck
```

### Configure the milter in Postfix

The milter will listen on port 30073 at 127.0.0.1 by default. Add the milter in Postfix
to the smtpd_milters setting in the main.cf:

```
smtpd_milters = ..., inet:127.0.0.1:30073, ...
```

## Testing

If you have installed *miltertest* from the OpenDKIM project, you can run the
tests from the tests/ folder by simply calling the testing.sh script on a shell.

Enjoy
