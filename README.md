# About

*mailheadercheck* is a Postfix milter.

It checks some headers for RFC/BCP validity.

Based on the milter "verifyemail" of Christian Rößner:
 https://gitlab.roessner-net.de/croessner/verifyemail/

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
/etc/systemd/system/ and create a user named "milter":

```
sudo apt install python3-dev libmilter-dev python3-pip python3-yaml
sudo pip3 install pymilter
sudo cp mailheadercheck /usr/local/sbin/
sudo cp -r lib /usr/local/sbin/
sudo chmod 755 /usr/local/sbin/mailheadercheck
sudo cp mailheadercheck.service /etc/systemd/system/
sudo mkdir /etc/mailheadercheck
sudo cp config.yaml /etc/mailheadercheck
sudo useradd milter -r -s /bin/false
mailheadercheck --help
```

## Configuration file

The YAML configuration file will be read from the following locations:
- a path given by the --config parameter
- /etc/mailheadercheck/config.yaml
- ./config.yaml

If there is no config file found, the program exits.

## Configuration options

**Please edit the default config.yaml according to your needs!**

### debug

debug=0 only outputs the "summary line" at the end with the results.

debug=1 additionally outputs some log lines for each check that is run.

### dry_run

The milter has a dry-run mode which can be activated by globally setting "dry_run" to "1" in the config file.

If there is no setting found in the config.yaml, dry-run is active by default.

Additionally you can change the "dry_run" setting in each check individually. With this you can either set "dry_run"
globally to 1, and then individual checks to 0. Or the other way around.

### log_target

You can choose from the following log targets:

- syslog (also set "syslog_name" and "syslog_facility" then)
- stdout (for Docker)
- file (also set "log_filepath" then)

### log_format

This can be set to either "plain" or "json". This only affects the "summary line" when debug=0. It does not
affect the DEBUG log lines which are written when debug=1.

### log_privacy_mode

Setting "log_privacy_mode" to 1 activates the privacy mode, which does not write the Subject:-header or
From:-header to the logfile.

### socket

The "socket" setting can have one of the following formats:

- inet:port@ipv4
- inet6:port@ipv6
- unix:/path/to/socket

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

Enjoy
