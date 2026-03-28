from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import Milter
import json
import random
import string
import time
from mailheaderchecklib.utility import CheckUtils, Logger, Cfg
from mailheaderchecklib.checks import CHECKS
from mailheaderchecklib.metrics import (
    record_message, record_check_violation, record_eom_duration,
    record_connection_opened, record_connection_closed, record_exclusion_hit,
)


@dataclass
class _MessageState:
    headers: dict[str, str] = field(default_factory=dict)
    header_counter: dict[str, int] = field(default_factory=lambda: {
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
    })
    envelope_from: str = ''
    sasl_username: str | None = None


# noinspection PyIncorrectDocstring,PyUnresolvedReferences
class MailHeaderCheckMilter(Milter.Base):
    """
    Milter that verifies RFC/BCP validity of some headers (Date, Subject, From, Message-ID, ...)
    """

    def __init__(self) -> None:
        self.__config: dict[str, Any] = Cfg.config
        self.__logging: Any = Cfg.logging
        self.__connection_id: str = ''
        self.__ip: str | None = None
        self.__msg: _MessageState = _MessageState()
        try:
            self.__dry_run_active = bool(self.__config['dry_run'])
        except (KeyError, TypeError):
            self.__dry_run_active = True

    @Milter.noreply
    def connect(self, ipname: str, family: int, hostaddr: tuple[str, int]) -> int:
        self.__connection_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
        self.__ip = hostaddr[0]
        port = hostaddr[1]
        self.__logging.debug(self.__connection_id + ' Connection received: Hostname="' + ipname + '" IP="' + self.__ip + '" Port=' + str(port))
        record_connection_opened()
        return Milter.CONTINUE

    def close(self) -> int:
        record_connection_closed()
        return Milter.CONTINUE

    @Milter.noreply
    def envfrom(self, mailfrom: str, *dummy: Any) -> int:
        """ Callback that is called when MAIL FROM: is recognized. """
        self.__msg = _MessageState()
        self.__msg.envelope_from = mailfrom
        try:
            self.__msg.sasl_username = self.getsymval('auth_authen')
            if not self.__msg.sasl_username:
                self.__msg.sasl_username = self.getsymval('{auth_authen}')
        except Exception:
            self.__msg.sasl_username = None
        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name: str, hval: str) -> int:
        """ header callback gets called for each header """
        if name.lower() in self.__msg.header_counter:
            self.__msg.header_counter[name.lower()] += 1
            self.__msg.headers[name.lower()] = hval
        return Milter.CONTINUE

    def eom(self) -> int:
        """ end of message. Gets called after end of the message body """

        eom_start = time.perf_counter()
        check_result = 'accept'
        actiontaken = 'accept'
        failedChecks = []

        for check in CHECKS:
            if not CheckUtils.check_is_enabled(self.__config, check.name):
                self.__logging.debug(self.__connection_id+' Check "'+check.name+'" is disabled (enabled=0), skipping')
                continue

            self.__logging.debug(self.__connection_id+' Running check: ' + check.niceName + '('+check.name+')')

            self.__logging.debug(self.__connection_id+' Check if the SASL username is on exclude_sasl_usernames list of check "'+check.name+'"')
            if CheckUtils.sasl_found_in_exclude_list(self.__config, self.__msg.sasl_username, check.name):
                self.__logging.debug(self.__connection_id+' SASL username in exclude list found, skipping this check...')
                record_exclusion_hit(check.name, 'sasl')
                continue

            self.__logging.debug(self.__connection_id+' Check if the sender address is on exclude_envelopefrom_addresses list of check "'+check.name+'"')
            if CheckUtils.envelopefrom_found_in_exclude_list(self.__config, self.__msg.envelope_from, check.name):
                self.__logging.debug(self.__connection_id+' Envelope-From in exclude list found, skipping this check...')
                record_exclusion_hit(check.name, 'envelopefrom')
                continue

            self.__logging.debug(self.__connection_id+' Check if the From: header address is on exclude_fromheader_addresses list of check "'+check.name+'"')
            if CheckUtils.fromheader_found_in_exclude_list(self.__config, self.__msg.headers, check.name):
                self.__logging.debug(self.__connection_id+' From header address in exclude list found, skipping this check...')
                record_exclusion_hit(check.name, 'fromheader')
                continue

            self.__logging.debug(self.__connection_id+' Check if the sender domain is on exclude domain list of check "'+check.name+'"')
            if CheckUtils.domain_found_in_exclude_list(self.__config, self.__msg.headers, self.__msg.envelope_from, check.name):
                self.__logging.debug(self.__connection_id+' Domain in one of the exclude domain lists found, skipping this check...')
                record_exclusion_hit(check.name, 'domain')
                continue

            self.__logging.debug(self.__connection_id+' Check if the IP address is on exclude_ips list of check "'+check.name+'"')
            if CheckUtils.ip_found_in_exclude_ip_list(self.__config, self.__ip, check.name):
                self.__logging.debug(self.__connection_id+' IP in exclude_ip list found, skipping this check...')
                record_exclusion_hit(check.name, 'ip')
                continue

            self.__logging.debug(self.__connection_id+' Doing the check now...')
            check_response = check.fn(self.__msg.headers, self.__msg.header_counter, self.__config)
            self.__logging.debug(self.__connection_id+' Check result: ' + str(check_response))
            if check_response == True:
                check_result = 'reject'
                failedChecks.append(check.niceName)
                record_check_violation(check.name)
                if CheckUtils.single_check_dry_run_active(self.__config, check.name):
                    self.__logging.debug(self.__connection_id+' This check returned a reject, BUT the check is marked as "dry_run=1". Proceeding with checks...')
                elif self.__dry_run_active == False:
                    actiontaken = 'reject'
                    self.__logging.debug(self.__connection_id+' This check returned a reject, we skip remaining checks')
                    break
                else:
                    self.__logging.debug(self.__connection_id+' This check returned a reject, BUT global dry-run is active. Proceeding with checks...')

        failedCheckStr = ', '.join(failedChecks)
        record_eom_duration(time.perf_counter() - eom_start)
        record_message(check_result, actiontaken, self.__dry_run_active)

        if actiontaken == 'reject':
            self.setreply("554", xcode="5.7.0", msg="Header violation: " + failedChecks[-1])

        """ Prepare headers for log output """
        if 'from' not in self.__msg.headers:
            fromHeader = 'missing-from-header'
        elif self.__msg.header_counter['from'] > 1:
            fromHeader = 'multiple-from-headers'
        elif Logger.getLogPrivacyMode(self.__config):
            fromHeader = 'privacy-mode-active'
        else:
            fromHeader = self.__msg.headers['from'].replace('\n', ' ').replace('\r', '')

        if 'subject' not in self.__msg.headers:
            subjectHeader = 'missing-subject-header'
        elif self.__msg.header_counter['subject'] > 1:
            subjectHeader = 'multiple-subject-headers'
        elif Logger.getLogPrivacyMode(self.__config):
            subjectHeader = 'privacy-mode-active'
        else:
            subjectHeader = (self.__msg.headers['subject'][:200] + '...') if len(self.__msg.headers['subject']) > 200 else self.__msg.headers['subject']
            subjectHeader = subjectHeader.replace('\n', ' ').replace('\r', '')

        if 'date' not in self.__msg.headers:
            dateHeader = 'missing-date-header'
        elif self.__msg.header_counter['date'] > 1:
            dateHeader = 'multiple-date-headers'
        else:
            dateHeader = self.__msg.headers['date'].replace('\n', ' ').replace('\r', '')

        if self.__config['log_format'] == 'json':
            log_output = json.dumps({
                'connection_id': self.__connection_id,
                'queue_id': self.getsymval('i'),
                'client_ip': self.__ip,
                'sasl_username': self.__msg.sasl_username,
                'envelope_from': self.__msg.envelope_from,
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
                self.__connection_id,
                self.getsymval('i'),
                (self.__ip or '').replace('"', '\''),
                (self.__msg.sasl_username or '').replace('"', '\''),
                (self.__msg.envelope_from or '').replace('"', '\''),
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
                'connection_id': self.__connection_id,
                'queue_id': self.getsymval('i'),
                'error_response_text': failedCheckStr,
                'result': check_result,
                'actiontaken': actiontaken,
                'dry_run': 'yes' if self.__dry_run_active else 'no'
            })
            self.addheader('X-MailHeaderCheck', header_output)

        return Milter.ACCEPT if actiontaken == 'accept' else Milter.REJECT

# vim: expandtab ts=4 sw=4
