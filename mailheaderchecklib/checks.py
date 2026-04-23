"""Check functions and registry for mailheadercheck."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from email.utils import parsedate, getaddresses
from typing import Any


CheckFn = Callable[[dict[str, str], dict[str, int], dict[str, Any]], bool]


@dataclass(frozen=True)
class Check:
    """Represents a single header check with a name, display name, and check function."""

    name: str
    nice_name: str
    fn: CheckFn


# ── helpers (called only from check functions below) ─────────────────────────

def _not_exactly_one_address_in_from(headers: dict[str, str]) -> bool:
    """Called only when exactly one non-empty From header is present."""
    try:
        all_emails = getaddresses([headers['from']])
        unique_addresses = {addr.lower() for _, addr in all_emails if '@' in addr}
        return len(unique_addresses) != 1
    except (ValueError, TypeError, KeyError):
        return False


def _is_date_invalid(headers: dict[str, str]) -> bool:
    """Called only when exactly one Date header is present."""
    try:
        return parsedate(headers['date']) is None
    except (ValueError, TypeError, KeyError):
        return False


def _is_subject_too_long(headers: dict[str, str], config: dict[str, Any]) -> bool:
    """Called only when exactly one Subject header is present."""
    try:
        max_length = int(config['checks']['long_subject_header']['max_length'])
    except (KeyError, TypeError, ValueError):
        max_length = 5000
    return len(headers['subject']) > max_length


# ── check functions ───────────────────────────────────────────────────────────

def _check_missing_from_header(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('from', 0) == 0


def _check_multiple_from_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('from', 0) > 1


def _check_empty_from_header(
    headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('from', 0) == 1 and len(headers['from'].strip()) == 0


def _check_not_exactly_one_address_in_from_header(
    headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return (counter.get('from', 0) == 1
            and len(headers['from'].strip()) > 0
            and _not_exactly_one_address_in_from(headers))


def _check_multiple_subject_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('subject', 0) > 1


def _check_long_subject_header(
    headers: dict[str, str], counter: dict[str, int], config: dict[str, Any]
) -> bool:
    return counter.get('subject', 0) == 1 and _is_subject_too_long(headers, config)


def _check_missing_date_header(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('date', 0) == 0


def _check_multiple_date_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('date', 0) > 1


def _check_empty_date_header(
    headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('date', 0) == 1 and len(headers['date'].strip()) == 0


def _check_invalid_date_header(
    headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('date', 0) == 1 and _is_date_invalid(headers)


def _check_multiple_sender_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('sender', 0) > 1


def _check_multiple_replyto_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('reply-to', 0) > 1


def _check_multiple_to_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('to', 0) > 1


def _check_multiple_cc_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('cc', 0) > 1


def _check_missing_messageid_header(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('message-id', 0) == 0


def _check_multiple_messageid_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('message-id', 0) > 1


def _check_multiple_inreplyto_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('in-reply-to', 0) > 1


def _check_multiple_references_headers(
    _headers: dict[str, str], counter: dict[str, int], _config: dict[str, Any]
) -> bool:
    return counter.get('references', 0) > 1


# ── check registry ────────────────────────────────────────────────────────────

CHECKS: list[Check] = [
    Check('missing_from_header', 'Missing From:-Header',
          _check_missing_from_header),
    Check('multiple_from_headers', 'Multiple From:-Headers',
          _check_multiple_from_headers),
    Check('empty_from_header', 'Empty From:-Header',
          _check_empty_from_header),
    Check('not_exactly_one_address_in_from_header',
          'Not exactly one address in From:-Header',
          _check_not_exactly_one_address_in_from_header),
    Check('multiple_subject_headers', 'Multiple Subject:-Headers',
          _check_multiple_subject_headers),
    Check('long_subject_header', 'Subject:-Header too long',
          _check_long_subject_header),
    Check('missing_date_header', 'Missing Date:-Header',
          _check_missing_date_header),
    Check('multiple_date_headers', 'Multiple Date:-Headers',
          _check_multiple_date_headers),
    Check('empty_date_header', 'Empty Date:-Header',
          _check_empty_date_header),
    Check('invalid_date_header', 'Invalid Date:-Header',
          _check_invalid_date_header),
    Check('multiple_sender_headers', 'Multiple Sender:-Headers',
          _check_multiple_sender_headers),
    Check('multiple_replyto_headers', 'Multiple Reply-To:-Headers',
          _check_multiple_replyto_headers),
    Check('multiple_to_headers', 'Multiple To:-Headers',
          _check_multiple_to_headers),
    Check('multiple_cc_headers', 'Multiple Cc:-Headers',
          _check_multiple_cc_headers),
    Check('missing_messageid_header', 'Missing Message-ID:-Header',
          _check_missing_messageid_header),
    Check('multiple_messageid_headers', 'Multiple Message-ID:-Headers',
          _check_multiple_messageid_headers),
    Check('multiple_inreplyto_headers', 'Multiple In-Reply-To:-Header',
          _check_multiple_inreplyto_headers),
    Check('multiple_references_headers', 'Multiple References:-Headers',
          _check_multiple_references_headers),
]

# vim: expandtab ts=4 sw=4
