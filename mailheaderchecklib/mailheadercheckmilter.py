"""Milter implementation for mailheadercheck."""
from __future__ import annotations

import json
import random
import string
import time
from dataclasses import dataclass, field
from typing import Any

import Milter

from mailheaderchecklib.checks import CHECKS
from mailheaderchecklib.metrics import (
    record_message, record_check_violation, record_eom_duration,
    record_connection_opened, record_connection_closed, record_exclusion_hit,
)
from mailheaderchecklib.utility import CheckUtils, Logger, Cfg


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
    # pylint: disable=no-member  # Milter is a C extension; CONTINUE/ACCEPT/REJECT are valid

    def __init__(self) -> None:
        self.__config: dict[str, Any] = Cfg.config or {}
        self.__logging: Any = Cfg.logging
        self.__connection_id: str = ''
        self.__ip: str | None = None
        self.__msg: _MessageState = _MessageState()
        try:
            self.__dry_run_active = bool(self.__config['dry_run'])
        except (KeyError, TypeError):
            self.__dry_run_active = True

    @Milter.noreply
    def connect(  # pylint: disable=arguments-renamed
            self, ipname: str, _family: int, hostaddr: tuple[str, int]) -> int:
        """Callback invoked when a new SMTP connection is accepted."""
        self.__connection_id = ''.join(
            random.choices(string.ascii_uppercase + string.digits, k=12)
        )
        self.__ip = hostaddr[0]
        port = hostaddr[1]
        self.__logging.debug(
            '%s Connection received: Hostname="%s" IP="%s" Port=%s',
            self.__connection_id, ipname, self.__ip, port
        )
        record_connection_opened()
        return Milter.CONTINUE

    def close(self) -> int:
        """Callback invoked when the SMTP connection is closed."""
        if self.__ip is not None:
            record_connection_closed()
        return Milter.CONTINUE

    @Milter.noreply
    def envfrom(self, mailfrom: str, *_: Any) -> int:  # pylint: disable=arguments-differ
        """ Callback that is called when MAIL FROM: is recognized. """
        self.__msg = _MessageState()
        self.__msg.envelope_from = mailfrom
        try:
            self.__msg.sasl_username = self.getsymval('auth_authen')
            if not self.__msg.sasl_username:
                self.__msg.sasl_username = self.getsymval('{auth_authen}')
        except Exception:  # pylint: disable=broad-exception-caught
            self.__msg.sasl_username = None
        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name: str, hval: str) -> int:  # pylint: disable=arguments-renamed
        """ header callback gets called for each header """
        if name.lower() in self.__msg.header_counter:
            self.__msg.header_counter[name.lower()] += 1
            self.__msg.headers[name.lower()] = hval
        return Milter.CONTINUE

    def eom(self) -> int:
        """ end of message. Gets called after end of the message body """
        # pylint: disable=too-many-branches,too-many-statements,too-many-locals

        eom_start = time.perf_counter()
        check_result = 'accept'
        actiontaken = 'accept'
        failed_checks = []

        for check in CHECKS:
            if not CheckUtils.check_is_enabled(self.__config, check.name):
                self.__logging.debug(
                    '%s Check "%s" is disabled (enabled=0), skipping',
                    self.__connection_id, check.name
                )
                continue

            self.__logging.debug(
                '%s Running check: %s (%s)',
                self.__connection_id, check.nice_name, check.name
            )

            self.__logging.debug(
                '%s Check if the SASL username is on exclude_sasl_usernames'
                ' list of check "%s"',
                self.__connection_id, check.name
            )
            if CheckUtils.sasl_found_in_exclude_list(
                    self.__config, self.__msg.sasl_username, check.name):
                self.__logging.debug(
                    '%s SASL username in exclude list found, skipping this check...',
                    self.__connection_id
                )
                record_exclusion_hit(check.name, 'sasl')
                continue

            self.__logging.debug(
                '%s Check if the sender address is on exclude_envelopefrom_addresses'
                ' list of check "%s"',
                self.__connection_id, check.name
            )
            if CheckUtils.envelopefrom_found_in_exclude_list(
                    self.__config, self.__msg.envelope_from, check.name):
                self.__logging.debug(
                    '%s Envelope-From in exclude list found, skipping this check...',
                    self.__connection_id
                )
                record_exclusion_hit(check.name, 'envelopefrom')
                continue

            self.__logging.debug(
                '%s Check if the From: header address is on exclude_fromheader_addresses'
                ' list of check "%s"',
                self.__connection_id, check.name
            )
            if CheckUtils.fromheader_found_in_exclude_list(
                    self.__config, self.__msg.headers, check.name):
                self.__logging.debug(
                    '%s From header address in exclude list found, skipping this check...',
                    self.__connection_id
                )
                record_exclusion_hit(check.name, 'fromheader')
                continue

            self.__logging.debug(
                '%s Check if the sender domain is on exclude domain list of check "%s"',
                self.__connection_id, check.name
            )
            if CheckUtils.domain_found_in_exclude_list(
                    self.__config, self.__msg.headers,
                    self.__msg.envelope_from, check.name):
                self.__logging.debug(
                    '%s Domain in one of the exclude domain lists found,'
                    ' skipping this check...',
                    self.__connection_id
                )
                record_exclusion_hit(check.name, 'domain')
                continue

            self.__logging.debug(
                '%s Check if the IP address is on exclude_ips list of check "%s"',
                self.__connection_id, check.name
            )
            if CheckUtils.ip_found_in_exclude_ip_list(self.__config, self.__ip, check.name):
                self.__logging.debug(
                    '%s IP in exclude_ip list found, skipping this check...',
                    self.__connection_id
                )
                record_exclusion_hit(check.name, 'ip')
                continue

            self.__logging.debug('%s Doing the check now...', self.__connection_id)
            check_response = check.fn(self.__msg.headers, self.__msg.header_counter, self.__config)
            self.__logging.debug('%s Check result: %s', self.__connection_id, check_response)
            if check_response:
                check_result = 'reject'
                failed_checks.append(check.nice_name)
                record_check_violation(check.name)
                if CheckUtils.single_check_dry_run_active(self.__config, check.name):
                    self.__logging.debug(
                        '%s This check returned a reject, BUT the check is'
                        ' marked as "dry_run=1". Proceeding with checks...',
                        self.__connection_id
                    )
                elif not self.__dry_run_active:
                    actiontaken = 'reject'
                    self.__logging.debug(
                        '%s This check returned a reject, we skip remaining checks',
                        self.__connection_id
                    )
                    break
                else:
                    self.__logging.debug(
                        '%s This check returned a reject, BUT global dry-run'
                        ' is active. Proceeding with checks...',
                        self.__connection_id
                    )

        failed_check_str = ', '.join(failed_checks)
        record_eom_duration(time.perf_counter() - eom_start)
        record_message(check_result, actiontaken, self.__dry_run_active)

        if actiontaken == 'reject':
            self.setreply("554", xcode="5.7.0", msg="Header violation: " + failed_checks[-1])

        # Prepare headers for log output
        if 'from' not in self.__msg.headers:
            from_header = 'missing-from-header'
        elif self.__msg.header_counter['from'] > 1:
            from_header = 'multiple-from-headers'
        elif Logger.get_log_privacy_mode(self.__config):
            from_header = 'privacy-mode-active'
        else:
            from_header = self.__msg.headers['from'].replace('\n', ' ').replace('\r', '')

        if 'subject' not in self.__msg.headers:
            subject_header = 'missing-subject-header'
        elif self.__msg.header_counter['subject'] > 1:
            subject_header = 'multiple-subject-headers'
        elif Logger.get_log_privacy_mode(self.__config):
            subject_header = 'privacy-mode-active'
        else:
            subject_header = self.__msg.headers['subject']
            if len(subject_header) > 200:
                subject_header = subject_header[:200] + '...'
            subject_header = subject_header.replace('\n', ' ').replace('\r', '')

        if 'date' not in self.__msg.headers:
            date_header = 'missing-date-header'
        elif self.__msg.header_counter['date'] > 1:
            date_header = 'multiple-date-headers'
        else:
            date_header = self.__msg.headers['date'].replace('\n', ' ').replace('\r', '')

        if self.__config['log_format'] == 'json':
            log_output = json.dumps({
                'connection_id': self.__connection_id,
                'queue_id': self.getsymval('i'),
                'client_ip': self.__ip,
                'sasl_username': self.__msg.sasl_username,
                'envelope_from': self.__msg.envelope_from,
                'header_from': from_header,
                'header_subject': subject_header,
                'header_date': date_header,
                'error_response_text': failed_check_str,
                'result': check_result,
                'actiontaken': actiontaken,
                'dry_run': 'yes' if self.__dry_run_active else 'no'
            })
        else:
            ip_val = (self.__ip or '').replace('"', "'")
            sasl_val = (self.__msg.sasl_username or '').replace('"', "'")
            env_val = (self.__msg.envelope_from or '').replace('"', "'")
            from_val = from_header.replace('"', "'")
            subj_val = subject_header.replace('"', "'")
            log_output = (
                f'connection_id={self.__connection_id}'
                f' queue_id={self.getsymval("i")}'
                f' client_ip="{ip_val}"'
                f' sasl_username="{sasl_val}"'
                f' envelope_from="{env_val}"'
                f' header_from="{from_val}"'
                f' header_subject="{subj_val}"'
                f' header_date="{date_header}"'
                f' error_response_text="{failed_check_str}"'
                f' result={check_result}'
                f' actiontaken={actiontaken}'
                f' dry_run={"yes" if self.__dry_run_active else "no"}'
            )
        self.__logging.info(log_output)

        if 'add_result_header' in self.__config and self.__config['add_result_header'] == 1:
            header_output = json.dumps({
                'connection_id': self.__connection_id,
                'queue_id': self.getsymval('i'),
                'error_response_text': failed_check_str,
                'result': check_result,
                'actiontaken': actiontaken,
                'dry_run': 'yes' if self.__dry_run_active else 'no'
            })
            self.addheader('X-MailHeaderCheck', header_output)

        return Milter.ACCEPT if actiontaken == 'accept' else Milter.REJECT

# vim: expandtab ts=4 sw=4
