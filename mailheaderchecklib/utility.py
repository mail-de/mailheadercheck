"""Utility classes and configuration for mailheadercheck."""
from __future__ import annotations

from email.utils import getaddresses
from typing import Any
import logging
import logging.handlers
import ipaddress
import sys
import yaml


class CheckUtils:
    """Static utility methods for evaluating per-check exclusion lists and flags."""

    @staticmethod
    def domain_found_in_exclude_list(
            config: dict[str, Any], headers: dict[str, str],
            envelope_from: str, check_name: str) -> bool:
        """Return True if the envelope-from or From-header domain is in an exclude list."""
        # check exclude_envelopefrom_domains
        try:
            exclude_envelopefrom_domains = [
                domain.lower()
                for domain in config['checks'][check_name]['exclude_envelopefrom_domains']
            ]
            envelope_from = envelope_from.strip('<>')
            domain = envelope_from[envelope_from.index('@') + 1:].lower()
            if domain in exclude_envelopefrom_domains:
                return True
        except KeyError:
            pass
        except TypeError:
            #  TypeError: "'NoneType' object is not subscriptable"
            pass
        except ValueError:   # substring '@' not found
            pass

        # check exclude_fromheader_domains
        if 'from' not in headers:
            return False
        try:
            exclude_fromheader_domains = [
                domain.lower()
                for domain in config['checks'][check_name]['exclude_fromheader_domains']
            ]
            all_emails = getaddresses([headers['from']])
            for email_addr in all_emails:
                # getaddresses returns (name, email) tuples
                _, emailaddress = email_addr
                domain = emailaddress[emailaddress.index('@') + 1:].lower()
                if domain in exclude_fromheader_domains:
                    return True
        except KeyError:
            pass
        except TypeError:
            #  TypeError: "'NoneType' object is not subscriptable"
            pass
        except ValueError:   # substring '@' not found
            pass

        return False

    @staticmethod
    def envelopefrom_found_in_exclude_list(
            config: dict[str, Any], envelope_from: str, check_name: str) -> bool:
        """Return True if the envelope-from address is in the exclude list."""
        # check exclude_envelopefrom_addresses (full addresses)
        try:
            exclude_envelopefrom_addresses = [
                addr.lower()
                for addr in config['checks'][check_name]['exclude_envelopefrom_addresses']
            ]
            envelope_from_norm = envelope_from.strip('<>').lower()
            if envelope_from_norm in exclude_envelopefrom_addresses:
                return True
        except KeyError:
            pass
        except TypeError:
            pass
        return False

    @staticmethod
    def fromheader_found_in_exclude_list(
            config: dict[str, Any], headers: dict[str, str], check_name: str) -> bool:
        """Return True if any From-header address is in the exclude list."""
        # check exclude_fromheader_addresses (full addresses from From: header)
        if 'from' not in headers:
            return False
        try:
            exclude_fromheader_addresses = [
                addr.lower()
                for addr in config['checks'][check_name]['exclude_fromheader_addresses']
            ]
            all_emails = getaddresses([headers['from']])
            for _, emailaddress in all_emails:
                if emailaddress and emailaddress.lower() in exclude_fromheader_addresses:
                    return True
        except KeyError:
            pass
        except TypeError:
            pass
        return False

    @staticmethod
    def sasl_found_in_exclude_list(
            config: dict[str, Any], sasl_username: str | None, check_name: str) -> bool:
        """Return True if the SASL username is in the exclude list."""
        # check exclude_sasl_usernames
        if not sasl_username:
            return False
        try:
            exclude_sasl_usernames = [
                u.lower()
                for u in config['checks'][check_name]['exclude_sasl_usernames']
            ]
            if sasl_username.lower() in exclude_sasl_usernames:
                return True
        except KeyError:
            pass
        except TypeError:
            pass
        return False

    @staticmethod
    def ip_found_in_exclude_ip_list(
            config: dict[str, Any], ip: str, check_name: str) -> bool:
        """Return True if the client IP matches an entry in the exclude_ips list."""
        # check if exclude_ips has been configured for this check
        try:
            exclude_ip_list = config['checks'][check_name]['exclude_ips']
            for exclude_ip in exclude_ip_list:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(exclude_ip):
                    return True
        except KeyError:
            pass
        except TypeError:
            #  TypeError: "'NoneType' object is not subscriptable"
            pass

        return False

    @staticmethod
    def single_check_dry_run_active(config: dict[str, Any], check_name: str) -> bool:
        """Return True if dry_run is set to 1 for the given check."""
        try:
            action_value = config['checks'][check_name]['dry_run']
        except KeyError:
            return False
        except TypeError:
            #  TypeError: "'NoneType' object is not subscriptable"
            return False

        if str(action_value) == '1':   # cast to str so users can use integers or strings
            return True
        return False

    @staticmethod
    def check_is_enabled(config: dict[str, Any], check_name: str) -> bool:
        """Return True if the check is enabled (enabled != 0)."""
        try:
            enabled_value = config['checks'][check_name]['enabled']
        except KeyError:
            return True
        except TypeError:
            #  TypeError: "'NoneType' object is not subscriptable"
            return True

        if str(enabled_value) == '0':   # cast to str so users can use integers or strings
            return False
        return True


class Logger:
    """Factory for creating configured Python logger instances."""

    @staticmethod
    def get_syslog_logger(config: dict[str, Any]) -> logging.Logger:
        """Return a logger that writes to syslog."""
        log = logging.getLogger(config['syslog_name'])
        log.setLevel(Logger.get_log_level(config))
        handler = logging.handlers.SysLogHandler(
            address='/dev/log', facility=config['syslog_facility']
        )
        if config['log_format'] == 'json':
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter('%(name)s[%(process)d]: %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        return log

    @staticmethod
    def get_file_logger(config: dict[str, Any]) -> Any:
        """Return a logger that writes to a file."""
        if config['log_format'] == 'json':
            log_format = '%(message)s'
        else:
            log_format = '%(name)s[%(process)d]: %(message)s'
        logging.basicConfig(
            format=log_format,
            filename=config['log_filepath'],
            level=Logger.get_log_level(config),
            encoding='utf-8',
        )
        return logging

    @staticmethod
    def get_stdout_logger(config: dict[str, Any]) -> Any:
        """Return a logger that writes to stdout."""
        if config['log_format'] == 'json':
            log_format = '%(message)s'
        else:
            log_format = '%(name)s[%(process)d]: %(message)s'
        logging.basicConfig(format=log_format, level=Logger.get_log_level(config))
        return logging

    @staticmethod
    def get_log_level(config: dict[str, Any]) -> int:
        """Return the logging level based on the debug config key."""
        try:
            level = logging.DEBUG if config['debug'] == 1 else logging.INFO
        except KeyError:
            level = logging.INFO
        return level

    @staticmethod
    def get_log_privacy_mode(config: dict[str, Any]) -> bool:
        """Return True if log_privacy_mode is enabled."""
        try:
            return config['log_privacy_mode'] == 1
        except KeyError:
            return True


class Cfg:
    """Helper class for loading and validating configuration."""

    config: dict[str, Any] | None = None
    logging: Any = None

    @staticmethod
    def find_and_parse_config_file(config_param: str) -> dict[str, Any]:
        """Locate, read, and parse the YAML config file; exit on error."""
        yaml_data_file = None

        if config_param:
            try:
                yaml_data_file = open(config_param, encoding='utf-8')  # noqa: WPS515
            except IOError:
                print('FATAL: config.yaml not found in ' + config_param + '! Exiting...')
                sys.exit(1)
        else:
            try:
                yaml_data_file = open(  # noqa: WPS515
                    '/etc/mailheadercheck/config.yaml', encoding='utf-8'
                )
            except IOError:
                try:
                    yaml_data_file = open('./config.yaml', encoding='utf-8')  # noqa: WPS515
                except IOError:
                    print(
                        'FATAL: config.yaml not found in /etc/mailheadercheck/'
                        ' or in the current folder! Exiting...'
                    )
                    sys.exit(1)

        try:
            with yaml_data_file as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(
                'FATAL: config.yaml could not be parsed.'
                ' Error message: "' + str(e) + '". Exiting...'
            )
            sys.exit(1)
        return config

    @staticmethod
    def validate_config(config: dict[str, Any], allowed_checks: set[str]) -> list[str]:
        """Validate config dict; return list of error strings (empty = valid)."""
        # pylint: disable=too-many-branches,too-many-statements,too-many-locals
        errors = []

        # log_target validation
        valid_log_targets = {'syslog', 'file', 'stdout'}
        lt = config.get('log_target')
        if lt not in valid_log_targets:
            errors.append(f"Invalid log_target '{lt}'. Allowed: syslog, file, stdout")

        # log_format validation
        lf = config.get('log_format')
        if lf not in ('plain', 'json'):
            errors.append(f"Invalid log_format '{lf}'. Allowed: plain, json")

        # debug validation
        debug_val = config.get('debug', 0)
        if debug_val not in (0, 1, '0', '1'):
            errors.append(f"Invalid debug value '{debug_val}'. Allowed: 0, 1")

        # log_privacy_mode validation
        lpm = config.get('log_privacy_mode', 1)
        if lpm not in (0, 1, '0', '1'):
            errors.append(f"Invalid log_privacy_mode value '{lpm}'. Allowed: 0, 1")

        # add_result_header validation
        arh = config.get('add_result_header', 0)
        if arh not in (0, 1, '0', '1'):
            errors.append(f"Invalid add_result_header value '{arh}'. Allowed: 0, 1")

        # socket validation: allow 'inet:<port>@<host>', 'inet6:<port>@<host>',
        # 'unix:<path>' or 'local:<path>'
        sock = config.get('socket', '')
        if isinstance(sock, str):
            if sock.startswith('inet:') or sock.startswith('inet6:'):
                try:
                    if sock.startswith('inet:'):
                        rest = sock[len('inet:'):]
                    else:
                        rest = sock[len('inet6:'):]
                    port_str, host = rest.split('@', 1)
                    port = int(port_str)
                    if port < 1 or port > 65535 or not host:
                        raise ValueError()
                except (ValueError, AttributeError):
                    errors.append(
                        f"Invalid socket format '{sock}'. Expected inet:<port>@<host>,"
                        " inet6:<port>@<host>, unix:<path> or local:<path>"
                    )
            elif sock.startswith('unix:') or sock.startswith('local:'):
                if sock.startswith('unix:'):
                    path = sock[len('unix:'):]
                else:
                    path = sock[len('local:'):]
                if not path:
                    errors.append(
                        f"Invalid socket format '{sock}'."
                        " Expected unix:<path> or local:<path>"
                    )
            else:
                errors.append(
                    f"Invalid socket format '{sock}'. Expected inet:<port>@<host>,"
                    " inet6:<port>@<host>, unix:<path> or local:<path>"
                )
        else:
            errors.append("Invalid socket value type. Expected string like 'inet:40000@localhost'")

        # checks section must be a dict
        checks_cfg = config.get('checks', {})
        if checks_cfg is None:
            checks_cfg = {}
        if not isinstance(checks_cfg, dict):
            errors.append("'checks' must be a mapping/dictionary")
            checks_cfg = {}

        # allowed per-check options
        common_allowed_options = {
            'exclude_envelopefrom_domains',
            'exclude_fromheader_domains',
            'exclude_envelopefrom_addresses',
            'exclude_fromheader_addresses',
            'exclude_sasl_usernames',
            'exclude_ips',
            'dry_run',
            'enabled',
        }
        # special per-check options
        per_check_specific = {
            'long_subject_header': {'max_length'}
        }

        # unknown check names/options
        for check_name, options in checks_cfg.items():
            if check_name not in allowed_checks:
                msg = (
                    f"Unknown check '{check_name}' configured;"
                    f" known checks: {', '.join(sorted(allowed_checks))}"
                )
                errors.append(msg)
                # Skip further option validation for unknown checks
                continue

            if options is None:
                # allow null/None meaning empty options
                options = {}
            if not isinstance(options, dict):
                errors.append(f"Options for check '{check_name}' must be a mapping/dictionary")
                continue

            allowed_opts = set(common_allowed_options)
            allowed_opts.update(per_check_specific.get(check_name, set()))
            for opt_key in options.keys():
                if opt_key not in allowed_opts:
                    msg = f"Unknown option '{opt_key}' in check '{check_name}'"
                    errors.append(msg)

            # simple type validations
            if 'dry_run' in options and options['dry_run'] not in (0, 1, '0', '1'):
                errors.append(
                    f"Invalid value for 'dry_run' in check '{check_name}': {options['dry_run']}"
                )
            if 'enabled' in options and options['enabled'] not in (0, 1, '0', '1'):
                errors.append(
                    f"Invalid value for 'enabled' in check '{check_name}': {options['enabled']}"
                )
            if check_name == 'long_subject_header' and 'max_length' in options:
                try:
                    ml = int(options['max_length'])
                    if ml < 1:
                        raise ValueError()
                except (ValueError, TypeError):
                    errors.append(
                        "'max_length' in 'long_subject_header' must be a positive integer"
                    )

        # metrics section validation
        metrics_cfg = config.get('metrics')
        if metrics_cfg is not None:
            if not isinstance(metrics_cfg, dict):
                errors.append("'metrics' must be a mapping/dictionary")
            else:
                allowed_metrics_keys = {'enabled', 'port', 'address'}
                for key in metrics_cfg:
                    if key not in allowed_metrics_keys:
                        errors.append(f"Unknown key '{key}' in 'metrics' section")

                me = metrics_cfg.get('enabled', 0)
                if me not in (0, 1, '0', '1'):
                    errors.append(f"Invalid metrics.enabled value '{me}'. Allowed: 0, 1")

                mp = metrics_cfg.get('port', 9182)
                try:
                    port_int = int(mp)
                    if port_int < 1 or port_int > 65535:
                        raise ValueError()
                except (ValueError, TypeError):
                    errors.append(
                        f"Invalid metrics.port value '{mp}'."
                        " Must be an integer between 1 and 65535"
                    )

                ma = metrics_cfg.get('address', '127.0.0.1')
                if not isinstance(ma, str) or not ma:
                    errors.append(
                        f"Invalid metrics.address value '{ma}'."
                        " Must be a non-empty string"
                    )

        return errors

# vim: expandtab ts=4 sw=4
