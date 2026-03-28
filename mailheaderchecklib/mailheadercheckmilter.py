from __future__ import annotations

from typing import Any
import Milter
import json
import random
import string
from mailheaderchecklib.utility import CheckUtils, Logger, Cfg
from mailheaderchecklib.checks import CHECKS

# noinspection PyIncorrectDocstring,PyUnresolvedReferences
class MailHeaderCheckMilter(Milter.Base):
    """
    Milter that verifies RFC/BCP validity of some headers (Date, Subject, From, Message-ID, ...)
    """

    def initializeHeaderCounter(self) -> None:
        self.__headerCounter = {
            'from': 0,
            'subject': 0,
            'date': 0,
            'sender': 0,
            'reply-to': 0,
            'to': 0,
            'cc': 0,
            'message-id': 0,
            'in-reply-to': 0,
            'references': 0,
        }

    def __init__(self) -> None:
        self.__config: dict[str, Any] = Cfg.config
        self.__logging: Any = Cfg.logging
        self.__headers: dict[str, str] = dict()
        self.__ipname: str | None = None
        self.__ip: str | None = None
        self.__port: int | None = None
        self.__sasl_username: str | None = None
        self.__connectionId: str = ''
        self.__envelopeFrom: str = ''
        self.__dry_run_active: bool = False
        self.__headerCounter: dict[str, int] = {}
        self.initializeHeaderCounter()

        try:
            self.__dry_run_active = bool(self.__config['dry_run'])
        except KeyError:     # if there is no "dry_run" entry in the config, we activate it
            self.__dry_run_active = True
        except TypeError:    #  TypeError: "'NoneType' object is not subscriptable". Happens if in yaml you don't configure empty dict, but Nothing/None
            self.__dry_run_active = True

    @Milter.noreply
    def connect(self, ipname: str, family: int, hostaddr: tuple[str, int]) -> int:
        alphabet = string.ascii_uppercase + string.digits
        self.__connectionId = ''.join(random.choices(alphabet, k=12))

        self.__ipname = ipname
        self.__ip = hostaddr[0]
        self.__port = hostaddr[1]

        self.__logging.debug(self.__connectionId+' Connection received: Hostname="'+self.__ipname+'" IP="'+self.__ip+'" Port='+str(self.__port))

        return Milter.CONTINUE

    @Milter.noreply
    def envfrom(self, mailfrom: str, *dummy: Any) -> int:
        """ Callback that is called when MAIL FROM: is recognized. """

        self.__headers = dict()
        self.__envelopeFrom = mailfrom
        # try to capture SASL username if available
        try:
            self.__sasl_username = self.getsymval('auth_authen')
            if not self.__sasl_username:
                self.__sasl_username = self.getsymval('{auth_authen}')
        except Exception:
            self.__sasl_username = None
        self.initializeHeaderCounter()

        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name: str, hval: str) -> int:
        """ header callback gets called for each header """

        if name.lower() in self.__headerCounter:
            self.__headerCounter[name.lower()] += 1
            self.__headers[name.lower()] = hval

        return Milter.CONTINUE

    def eom(self) -> int:
        """ end of message. Gets called after end of the message body """

        check_result = 'accept'
        actiontaken = 'accept'
        failedChecks = []

        for check in CHECKS:
            if not CheckUtils.check_is_enabled(self.__config, check.name):
                self.__logging.debug(self.__connectionId+' Check "'+check.name+'" is disabled (enabled=0), skipping')
                continue

            self.__logging.debug(self.__connectionId+' Running check: ' + check.niceName + '('+check.name+')')

            self.__logging.debug(self.__connectionId+' Check if the SASL username is on exclude_sasl_usernames list of check "'+check.name+'"')
            if CheckUtils.sasl_found_in_exclude_list(self.__config, self.__sasl_username, check.name):
                self.__logging.debug(self.__connectionId+' SASL username in exclude list found, skipping this check...')
                continue

            self.__logging.debug(self.__connectionId+' Check if the sender address is on exclude_envelopefrom_addresses list of check "'+check.name+'"')
            if CheckUtils.envelopefrom_found_in_exclude_list(self.__config, self.__envelopeFrom, check.name):
                self.__logging.debug(self.__connectionId+' Envelope-From in exclude list found, skipping this check...')
                continue

            self.__logging.debug(self.__connectionId+' Check if the From: header address is on exclude_fromheader_addresses list of check "'+check.name+'"')
            if CheckUtils.fromheader_found_in_exclude_list(self.__config, self.__headers, check.name):
                self.__logging.debug(self.__connectionId+' From header address in exclude list found, skipping this check...')
                continue

            self.__logging.debug(self.__connectionId+' Check if the sender domain is on exclude domain list of check "'+check.name+'"')
            if CheckUtils.domain_found_in_exclude_list(self.__config, self.__headers, self.__envelopeFrom, check.name):
                self.__logging.debug(self.__connectionId+' Domain in one of the exclude domain lists found, skipping this check...')
                continue

            self.__logging.debug(self.__connectionId+' Check if the IP address is on exclude_ips list of check "'+check.name+'"')
            if CheckUtils.ip_found_in_exclude_ip_list(self.__config, self.__ip, check.name):
                self.__logging.debug(self.__connectionId+' IP in exclude_ip list found, skipping this check...')
                continue

            self.__logging.debug(self.__connectionId+' Doing the check now...')
            check_response = check.fn(self.__headers, self.__headerCounter, self.__config)
            self.__logging.debug(self.__connectionId+' Check result: ' + str(check_response))
            if check_response == True:
                check_result = 'reject'
                failedChecks.append(check.niceName)
                if CheckUtils.single_check_dry_run_active(self.__config, check.name):
                    self.__logging.debug(self.__connectionId+' This check returned a reject, BUT the check is marked as "dry_run=1". Proceeding with checks...')
                elif self.__dry_run_active == False:
                    actiontaken = 'reject'
                    self.__logging.debug(self.__connectionId+' This check returned a reject, we skip remaining checks')
                    break
                else:
                    self.__logging.debug(self.__connectionId+' This check returned a reject, BUT global dry-run is active. Proceeding with checks...')

        failedCheckStr = ', '.join(failedChecks)

        if actiontaken == 'reject':
            self.setreply("554", xcode="5.7.0", msg="Header violation: " + failedChecks[-1])

        """ Prepare headers for log output """
        if 'from' not in self.__headers:
            fromHeader = 'missing-from-header'
        elif self.__headerCounter['from'] > 1:
            fromHeader = 'multiple-from-headers'
        elif Logger.getLogPrivacyMode(self.__config):
            fromHeader = 'privacy-mode-active'
        else:
            fromHeader = self.__headers['from'].replace('\n', ' ').replace('\r', '')

        if 'subject' not in self.__headers:
            subjectHeader = 'missing-subject-header'
        elif self.__headerCounter['subject'] > 1:
            subjectHeader = 'multiple-subject-headers'
        elif Logger.getLogPrivacyMode(self.__config):
            subjectHeader = 'privacy-mode-active'
        else:
            subjectHeader = (self.__headers['subject'][:200] + '...') if len(self.__headers['subject']) > 200 else self.__headers['subject']
            subjectHeader = subjectHeader.replace('\n', ' ').replace('\r', '')

        if 'date' not in self.__headers:
            dateHeader = 'missing-date-header'
        elif self.__headerCounter['date'] > 1:
            dateHeader = 'multiple-date-headers'
        else:
            dateHeader = self.__headers['date'].replace('\n', ' ').replace('\r', '')


        if self.__config['log_format'] == 'json':
            log_output = json.dumps({
                'connection_id': self.__connectionId,
                'queue_id': self.getsymval('i'),
                'client_ip': self.__ip,
                'sasl_username': self.__sasl_username,
                'envelope_from': self.__envelopeFrom,
                'header_from': fromHeader,
                'header_subject': subjectHeader,
                'header_date': dateHeader,
                'error_response_text': failedCheckStr,
                'result': check_result,
                'actiontaken': actiontaken,
                'dry_run': 'yes' if self.__dry_run_active else 'no'
            })
        else:
            log_output = "connection_id={0} queue_id={1} client_ip=\"{2}\" sasl_username=\"{3}\" envelope_from=\"{4}\" header_from=\"{5}\" header_subject=\"{6}\" header_date=\"{7}\" error_response_text=\"{8}\" result={9} actiontaken={10} dry_run={11}".format(
                self.__connectionId,
                self.getsymval('i'),
                (self.__ip or '').replace('"', '\''),
                (self.__sasl_username or '').replace('"', '\''),
                (self.__envelopeFrom or '').replace('"', '\''),
                fromHeader.replace('"', '\''),
                subjectHeader.replace('"', '\''),
                dateHeader,
                failedCheckStr,
                check_result,
                actiontaken,
                'yes' if self.__dry_run_active else 'no'
            )
        self.__logging.info(log_output)


        if 'add_result_header' in self.__config and self.__config['add_result_header'] == 1:
            header_output = json.dumps({
                'connection_id': self.__connectionId,
                'queue_id': self.getsymval('i'),
                'error_response_text': failedCheckStr,
                'result': check_result,
                'actiontaken': actiontaken,
                'dry_run': 'yes' if self.__dry_run_active else 'no'
            })
            self.addheader('X-MailHeaderCheck', header_output)

        return Milter.ACCEPT if actiontaken == 'accept' else Milter.REJECT

# vim: expandtab ts=4 sw=4
