"""Prometheus metrics support for mailheadercheck."""
from __future__ import annotations

import sys
from typing import Any

_MESSAGES_COUNTER = None
_VIOLATIONS_COUNTER = None
_RELOADS_COUNTER = None
_EOM_HISTOGRAM = None
_ACTIVE_CONNECTIONS_GAUGE = None
_EXCLUSIONS_COUNTER = None


def check_dependencies(config: dict[str, Any]) -> list[str]:
    """Return a list of dependency errors; empty means OK.

    Called during --configcheck so operators learn about missing packages
    before the milter is deployed.
    """
    metrics_cfg = config.get('metrics')
    if not isinstance(metrics_cfg, dict):
        return []
    if str(metrics_cfg.get('enabled', 0)) != '1':
        return []
    try:
        import prometheus_client  # noqa: F401  # pylint: disable=import-outside-toplevel,unused-import
        return []
    except ImportError:
        return [
            "metrics.enabled: 1 requires 'prometheus_client' "
            "(pip install prometheus_client  or  apt install python3-prometheus-client)"
        ]


def init_metrics(config: dict[str, Any], logging: Any, version: str = 'unknown') -> bool:
    """Initialise Prometheus metrics and start the HTTP scrape endpoint.

    Returns True if the endpoint was started, False if metrics are disabled.
    Hard-exits (sys.exit(1)) if metrics are enabled but prometheus_client
    is not installed. Must be called before Milter.runmilter().
    """
    # pylint: disable=global-statement
    global _MESSAGES_COUNTER, _VIOLATIONS_COUNTER, _RELOADS_COUNTER
    global _EOM_HISTOGRAM, _ACTIVE_CONNECTIONS_GAUGE, _EXCLUSIONS_COUNTER

    metrics_cfg = config.get('metrics') or {}
    if str(metrics_cfg.get('enabled', 0)) != '1':
        return False

    try:
        port = int(metrics_cfg.get('port', 9182))
    except (ValueError, TypeError):
        port = 9182
    address = str(metrics_cfg.get('address', '127.0.0.1'))

    try:
        # pylint: disable=import-outside-toplevel
        from prometheus_client import Counter, Gauge, Histogram, start_http_server
    except ImportError:
        print(
            "FATAL: metrics.enabled: 1 requires 'prometheus_client'. "
            "Install it with: pip install prometheus_client"
            "  or  apt install python3-prometheus-client"
        )
        sys.exit(1)

    _MESSAGES_COUNTER = Counter(
        'mailheadercheck_messages_total',
        'Total number of messages processed by the milter',
        ['result', 'actiontaken', 'dry_run'],
    )
    _VIOLATIONS_COUNTER = Counter(
        'mailheadercheck_check_violations_total',
        'Total number of check violations detected (regardless of dry_run or actiontaken)',
        ['check_name'],
    )
    _RELOADS_COUNTER = Counter(
        'mailheadercheck_config_reloads_total',
        'Total number of SIGHUP config reload attempts',
        ['result'],
    )
    info_gauge = Gauge(
        'mailheadercheck_info',
        'mailheadercheck version information',
        ['version'],
    )
    info_gauge.labels(version=version).set(1.0)

    _EOM_HISTOGRAM = Histogram(
        'mailheadercheck_eom_duration_seconds',
        'Time spent processing a message in eom() (end-of-data phase)',
        buckets=(.001, .005, .01, .025, .05, .1, .25, .5),
    )
    _ACTIVE_CONNECTIONS_GAUGE = Gauge(
        'mailheadercheck_active_connections',
        'Number of currently open SMTP connections to the milter',
    )
    _EXCLUSIONS_COUNTER = Counter(
        'mailheadercheck_exclusions_total',
        'Number of times a check was skipped due to an exclusion list match',
        ['check_name', 'exclusion_type'],
    )

    start_http_server(port, addr=address)
    logging.info(
        'mailheadercheck: Prometheus metrics endpoint started on %s:%s',
        address, port
    )
    return True


def record_message(result: str, actiontaken: str, dry_run: bool) -> None:
    """Increment the messages counter. No-op if metrics are disabled."""
    if _MESSAGES_COUNTER is None:
        return
    _MESSAGES_COUNTER.labels(
        result=result,
        actiontaken=actiontaken,
        dry_run='yes' if dry_run else 'no',
    ).inc()


def record_check_violation(check_name: str) -> None:
    """Increment the violations counter for a specific check. No-op if metrics are disabled."""
    if _VIOLATIONS_COUNTER is None:
        return
    _VIOLATIONS_COUNTER.labels(check_name=check_name).inc()


def record_config_reload(success: bool) -> None:
    """Increment the config reload counter. No-op if metrics are disabled."""
    if _RELOADS_COUNTER is None:
        return
    _RELOADS_COUNTER.labels(result='success' if success else 'failure').inc()


def record_eom_duration(duration: float) -> None:
    """Record the eom() processing time. No-op if metrics are disabled."""
    if _EOM_HISTOGRAM is None:
        return
    _EOM_HISTOGRAM.observe(duration)


def record_connection_opened() -> None:
    """Increment the active connections gauge. No-op if metrics are disabled."""
    if _ACTIVE_CONNECTIONS_GAUGE is None:
        return
    _ACTIVE_CONNECTIONS_GAUGE.inc()


def record_connection_closed() -> None:
    """Decrement the active connections gauge. No-op if metrics are disabled."""
    if _ACTIVE_CONNECTIONS_GAUGE is None:
        return
    _ACTIVE_CONNECTIONS_GAUGE.dec()


def record_exclusion_hit(check_name: str, exclusion_type: str) -> None:
    """Increment the exclusions counter. No-op if metrics are disabled."""
    if _EXCLUSIONS_COUNTER is None:
        return
    _EXCLUSIONS_COUNTER.labels(check_name=check_name, exclusion_type=exclusion_type).inc()

# vim: expandtab ts=4 sw=4
