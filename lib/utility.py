from email.utils import parsedate, getaddresses, parseaddr
import logging
import logging.handlers
import ipaddress
import sys
import yaml

class CheckUtils():
    def domain_found_in_exclude_list(config, headers, envelopeFrom, checkName):

        """ check exclude_envelopefrom_domains """
        try:
            exclude_envelopefrom_domains = [domain.lower() for domain in config['checks'][checkName]['exclude_envelopefrom_domains']]
            envelopeFrom = envelopeFrom.strip('<>')
            domain = envelopeFrom[envelopeFrom.index('@') + 1 : ].lower()
            if domain in exclude_envelopefrom_domains:
                return True
        except KeyError:
            pass
        except TypeError:    #  TypeError: "'NoneType' object is not subscriptable". Happens if in yaml you don't configure empty dict, but Nothing/None
            pass
        except ValueError:   # substring '@' not found
            pass

        """ check exclude_fromheader_domains """
        if 'from' not in headers:
            return False
        try:
            exclude_fromheader_domains = [domain.lower() for domain in config['checks'][checkName]['exclude_fromheader_domains']]
            all_emails = getaddresses([headers['from']])
            for email_addr in all_emails:
                name, emailaddress = parseaddr(email_addr)
                domain = emailaddress[emailaddress.index('@') + 1 : ].lower()
                if domain in exclude_fromheader_domains:
                    return True
        except KeyError:
            pass
        except TypeError:    #  TypeError: "'NoneType' object is not subscriptable". Happens if in yaml you don't configure empty dict, but Nothing/None
            pass
        except ValueError:   # substring '@' not found
            pass

        return False

    def ip_found_in_exclude_ip_list(config, ip, checkName):

        """ check if exclude_ips has been configured for this check """
        try:
            exclude_ip_list = config['checks'][checkName]['exclude_ips']
            for exclude_ip in exclude_ip_list:
                if ipaddress.ip_address(ip) in ipaddress.ip_network(exclude_ip):
                    return True
        except KeyError:
            pass
        except TypeError:    #  TypeError: "'NoneType' object is not subscriptable". Happens if in yaml you don't configure empty dict, but Nothing/None
            pass

        return False

    def single_check_dry_run_active(config, checkName):
        try:
            action_value = config['checks'][checkName]['dry_run']
        except KeyError:
            return False
        except TypeError:    #  TypeError: "'NoneType' object is not subscriptable". Happens if in yaml you don't configure empty dict, but Nothing/None
            return False

        if str(action_value) == '1':   # We cast to str here, so users can use integers or strings in config.json
            return True
        return False

    def not_exactly_one_address_in_from_header(config, headers):
        if 'from' not in headers:
            return False

        try:
            all_emails = getaddresses([headers['from']])
            all_emails = [x[1].lower() for x in all_emails]
            all_emails = set(all_emails)

            if len(all_emails) != 1:  # While technically RFC conform, we do not allow multiple addresses in the From:-header
                return True
        except Exception:
            # While parsing headers, there could be Exceptions.
            # If an Exception is thrown, we don't want the Milter to crash. For now, we simply ACCEPT the email.
            # Maybe in the future we block the email, because it's invalid/broken?
            return False
        return False

    def is_date_invalid(config, headers):
        if 'date' not in headers:
            return False

        try:
            if parsedate(headers['date']) == None:
                return True
        except Exception:
            # While parsing headers, there could be Exceptions.
            # If an Exception is thrown, we don't want the Milter to crash. For now, we simply ACCEPT the email.
            # Maybe in the future we block the email, because it's invalid/broken?
            return False
        return False

    def is_subject_too_long(config, headers):
        if 'subject' not in headers:
            return False

        try:
            max_length = config['checks']['long_subject_header']['max_length']
        except KeyError:
            max_length = 5000
        except TypeError:    #  TypeError: "'NoneType' object is not subscriptable". Happens if in yaml you don't configure empty dict, but Nothing/None
            max_length = 5000

        if len(headers['subject']) > max_length:
            return True
        return False

    def get_number_of_headers(headerCounter, headerName):
        if headerName in headerCounter:
            return headerCounter[headerName]
        else:
            return 0

class CheckRunner():
    def __init__(self, checkFunction):
        self.checkFunction = checkFunction
    def isValid(self, headers, headerCounter, config):
       return self.checkFunction(headers, headerCounter, config)

class Logger():
    def getSyslogLogger(config):
        log = logging.getLogger(config['syslog_name'])
        log.setLevel(Logger.getLogLevel(config))
        handler = logging.handlers.SysLogHandler(address = '/dev/log', facility = config['syslog_facility'])
        if config['log_format'] == 'json':
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter('%(name)s[%(process)d]: %(message)s')
        handler.setFormatter(formatter)
        log.addHandler(handler)
        return log

    def getFileLogger(config):
        if config['log_format'] == 'json':
            format = '%(message)s'
        else:
            format = '%(name)s[%(process)d]: %(message)s'
        logging.basicConfig(format=format, filename=config['log_filepath'], level=Logger.getLogLevel(config))
        return logging

    def getStdoutLogger(config):
        if config['log_format'] == 'json':
            format = '%(message)s'
        else:
            format = '%(name)s[%(process)d]: %(message)s'
        logging.basicConfig(format=format, level=Logger.getLogLevel(config))
        return logging

    def getLogLevel(config):
        try:
            level = logging.DEBUG if config['debug'] == 1 else logging.INFO
        except KeyError:
            level = logging.INFO
        return level

    def getLogPrivacyMode(config):
        try:
            return config['log_privacy_mode'] == 1
        except KeyError:
            return True


# noinspection PyUnresolvedReferences
class Cfg(object):
    """Helper class for some configuration parameters
    """
    config = None
    logging = None

    def find_and_parse_config_file(configParam):
        yaml_data_file = None

        if configParam:
            try:
                yaml_data_file = open(configParam)
            except IOError:
                print('FATAL: config.yaml not found in '+configParam+'! Exiting...')
                sys.exit(1)
        else:
            try:
                yaml_data_file = open('/etc/mailheadercheck/config.yaml')
            except IOError:
                try:
                    yaml_data_file = open('./config.yaml')
                except IOError:
                    print('FATAL: config.yaml not found in /etc/mailheadercheck/ or in the current folder! Exiting...')
                    sys.exit(1)

        try:
            with yaml_data_file as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print('FATAL: config.yaml could no be parsed. Error message: "'+e.msg+'". Exiting...')
            sys.exit(1)
        return config

# vim: expandtab ts=4 sw=4