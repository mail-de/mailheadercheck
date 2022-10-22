import Milter
import json
import random
import string
from lib.utility import CheckRunner, CheckUtils, Cfg

# noinspection PyIncorrectDocstring,PyUnresolvedReferences
class MailHeaderCheckMilter(Milter.Base):
    """
    Milter that verifies RFC/BCP validity of some headers (Date, Subject, From, Message-ID, ...)
    """

    allChecks = {
        'missing_from_header': {
            'niceName': "Missing From:-Header",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'from') == 0)
        },
        'multiple_from_headers': {
            'niceName': "Multiple From:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'from') > 1)
        },
        'not_exactly_one_address_in_from_header': {
            'niceName': "Not exactly one address in From:-Header",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'from') == 1 and CheckUtils.not_exactly_one_address_in_from_header(config, headers))
        },
        'multiple_subject_headers': {
            'niceName': "Multiple Subject:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'subject') > 1)
        },
        'long_subject_header': {
            'niceName': "Subject:-Header too long",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'subject') == 1 and CheckUtils.is_subject_too_long(config, headers))
        },
        'missing_date_header': {
            'niceName': "Missing Date:-Header",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'date') == 0)
        },
        'multiple_date_headers': {
            'niceName': "Multiple Date:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'date') > 1)
        },
        'empty_date_header': {
            'niceName': "Empty Date:-Header",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'date') == 1 and headers['date'] == '')
        },
        'invalid_date_header': {
            'niceName': "Invalid Date:-Header",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'date') == 1 and CheckUtils.is_date_invalid(config, headers))
        },
        'multiple_sender_headers': {
            'niceName': "Multiple Sender:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'sender') > 1)
        },
        'multiple_replyto_headers': {
            'niceName': "Multiple Reply-To:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'reply-to') > 1)
        },
        'multiple_to_headers': {
            'niceName': "Multiple To:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'to') > 1)
        },
        'multiple_cc_headers': {
            'niceName': "Multiple Cc:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'cc') > 1)
        },
        'missing_messageid_header': {
            'niceName': "Missing Message-ID:-Header",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'message-id') == 0)
        },
        'multiple_messageid_headers': {
            'niceName': "Multiple Message-ID:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'message-id') > 1)
        },
        'multiple_inreplyto_headers': {
            'niceName': "Multiple In-Reply-To:-Header",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'in-reply-to') > 1)
        },
        'multiple_references_headers': {
            'niceName': "Multiple References:-Headers",
            'check': CheckRunner(lambda headers, headerCounter, config: CheckUtils.get_number_of_headers(headerCounter, 'references') > 1)
        },
    }

    def initializeHeaderCounter(self):
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

    def __init__(self):
        self.__config = Cfg.config
        self.__logging = Cfg.logging
        self.__headers = dict()
        self.__ipname = None
        self.__ip = None
        self.__port = None
        self.initializeHeaderCounter()

        try:
            self.__dry_run_active = bool(self.__config['dry_run'])
        except KeyError:     # if there is no "dry_run" entry in the config, we activate it
            self.__dry_run_active = True
        except TypeError:    #  TypeError: "'NoneType' object is not subscriptable". Happens if in yaml you don't configure empty dict, but Nothing/None
            self.__dry_run_active = True

    @Milter.noreply
    def connect(self, ipname, family, hostaddr):
        alphabet = string.ascii_uppercase + string.digits
        self.__connectionId = ''.join(random.choices(alphabet, k=12))

        self.__ipname = ipname
        self.__ip = hostaddr[0]
        self.__port = hostaddr[1]

        self.__logging.debug(self.__connectionId+' Connection received: Hostname="'+self.__ipname+'" IP="'+self.__ip+'" Port='+str(self.__port))

        return Milter.CONTINUE

    @Milter.noreply
    def envfrom(self, mailfrom, *dummy):
        """ Callback that is called when MAIL FROM: is recognized. """

        self.__headers = dict()
        self.__envelopeFrom = mailfrom
        self.initializeHeaderCounter()

        return Milter.CONTINUE

    @Milter.noreply
    def header(self, name, hval):
        """ header callback gets called for each header """

        if name.lower() in self.__headerCounter:
            self.__headerCounter[name.lower()] += 1
            self.__headers[name.lower()] = hval

        return Milter.CONTINUE

    def eoh(self):
        """ end of header. Gets called after all headers have been processed """

        check_result = 'accept'
        actiontaken = 'accept'
        failedCheck = ''

        for checkName, oneCheck in self.allChecks.items():
            self.__logging.debug(self.__connectionId+' Running check: ' + oneCheck['niceName'] + '('+checkName+')')

            self.__logging.debug(self.__connectionId+' Check if the sender domain is on exclude domain list of check "'+checkName+'"')
            if CheckUtils.domain_found_in_exclude_list(self.__config, self.__headers, self.__envelopeFrom, checkName):
                self.__logging.debug(self.__connectionId+' Domain in one of the exclude domain lists found, skipping this check...')
                continue

            self.__logging.debug(self.__connectionId+' Check if the IP address is on exclude_ips list of check "'+checkName+'"')
            if CheckUtils.ip_found_in_exclude_ip_list(self.__config, self.__ip, checkName):
                self.__logging.debug(self.__connectionId+' IP in exclude_ip list found, skipping this check...')
                continue

            self.__logging.debug(self.__connectionId+' Doing the check now...')
            check_response = oneCheck['check'].isValid(self.__headers, self.__headerCounter, self.__config)
            self.__logging.debug(self.__connectionId+' Check result: ' + str(check_response))
            if check_response == True:
                check_result = 'reject'
                failedCheck = oneCheck['niceName']
                if CheckUtils.single_check_dry_run_active(self.__config, checkName):
                    self.__logging.debug(self.__connectionId+' This check returned a reject, BUT the check is marked as "dry_run=1". Proceeding with checks...')
                elif self.__dry_run_active == False:
                    actiontaken = 'reject'
                    self.__logging.debug(self.__connectionId+' This check returned a reject, we skip remaining checks')
                    break
                else:
                    self.__logging.debug(self.__connectionId+' This check returned a reject, BUT global dry-run is active. Proceeding with checks...')

        if actiontaken == 'reject':
            self.setreply("554", xcode="5.7.0", msg="Header violation: " + failedCheck)

        """ Prepare headers for log output """
        if 'from' not in self.__headers:
            fromHeader = 'missing-from-header'
        elif self.__headerCounter['from'] > 1:
            fromHeader = 'multiple-from-headers'
        elif self.__config['log_privacy_mode'] == 1:
            fromHeader = 'privacy-mode-active'
        else:
            fromHeader = self.__headers['from'].replace('\n', ' ').replace('\r', '')

        if 'subject' not in self.__headers:
            subjectHeader = 'missing-subject-header'
        elif self.__headerCounter['subject'] > 1:
            subjectHeader = 'multiple-subject-headers'
        elif self.__config['log_privacy_mode'] == 1:
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
                'qid': self.getsymval('i'),
                'header_from': fromHeader,
                'header_subject': subjectHeader,
                'header_date': dateHeader,
                'error_response_text': failedCheck,
                'result': check_result,
                'actiontaken': actiontaken,
                'dry_run': 'yes' if self.__dry_run_active else 'no'
            })
        else:
            log_output = "connection_id={0} qid={1} header_from=\"{2}\" header_subject=\"{3}\" header_date=\"{4}\" error_response_text=\"{5}\" result={6} actiontaken={7} dry_run={8}".format(
                self.__connectionId,
                self.getsymval('i'),
                fromHeader.replace('"', '\''),
                subjectHeader.replace('"', '\''),
                dateHeader,
                failedCheck,
                check_result,
                actiontaken,
                'yes' if self.__dry_run_active else 'no'
            )
        self.__logging.info(log_output)

        return Milter.ACCEPT if actiontaken == 'accept' else Milter.REJECT

# vim: expandtab ts=4 sw=4