# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

`mailheadercheck` is a Postfix milter that checks email headers for RFC/BCP validity. It uses `pymilter` (Python bindings for libmilter). When a check fails and `dry_run` is not active, the milter rejects the message with SMTP code `554 5.7.0`.

The main script is the executable `mailheadercheck` (no extension) which imports from `mailheaderchecklib/`.

## Running tests

Tests require `miltertest` (from the `miltertest` or `opendkim-tools` apt package) and Python dependencies from `requirements.txt`.

```sh
# Install Python dependencies
pip install -r requirements.txt

# Run all tests
./testing.sh

# Run a single miltertest functional test
miltertest -s tests/test-01.lua

# Run config syntax validation only
./mailheadercheck --config tests/config_syntax/syntaxtest-valid-01-config.yaml --configcheck
```

The `testing.sh` script runs two suites:
1. **Config syntax checks** — validates YAML configs in `tests/config_syntax/` using `--configcheck`. Each file has a `# result: valid|invalid` comment.
2. **Functional milter tests** — runs each `tests/test-*.lua` file via `miltertest`.

## Lint

```sh
pylint --disable=import-error mailheaderchecklib/ mailheadercheck
```

## Docker

```sh
# Build and start (tests run during Docker build)
docker compose up -d --build

# Validate config without starting the milter
docker compose run --rm mailheadercheck --config /config/config.yaml --configcheck
```

## Architecture

```
mailheadercheck            # Entry point (executable Python script)
mailheaderchecklib/
  checks.py                # Check dataclass, CheckFn type alias, all check functions, CHECKS registry
  mailheadercheckmilter.py # Milter class (MailHeaderCheckMilter extends Milter.Base)
  utility.py               # CheckUtils, Logger, Cfg
```

**Flow:** `mailheadercheck` (entry point) → reads and validates config via `Cfg` → sets up logger via `Logger` → registers `MailHeaderCheckMilter` with pymilter → milter callbacks: `connect()`, `envfrom()`, `header()`, `eom()`.

**Checks are defined** in `checks.py` as `Check` dataclass instances (`name`, `niceName`, `fn`) collected in the `CHECKS: list[Check]` registry. To add a new check, only `checks.py` needs to be edited: write a `_check_*` function and add a `Check(...)` entry to `CHECKS`. All check logic runs in `eom()` which iterates `CHECKS`.

**Per-check options** (under `checks.<check_name>`): `enabled` (0/1, default 1 — if 0, check is skipped entirely before any other processing), `dry_run` (0/1), and exclusion lists: `exclude_fromheader_domains`, `exclude_fromheader_addresses`, `exclude_envelopefrom_domains`, `exclude_envelopefrom_addresses`, `exclude_ips`, `exclude_sasl_usernames`. In `eom()`, `enabled` is checked first, then exclusion lists, then the check function itself.

**dry_run** can be set globally or per-check. If active, the check logs a would-be reject but continues and accepts the message. Default when not configured: dry_run is active.

**Config validation** (`Cfg.validate_config`) is invoked when `--configcheck` is passed and also on every normal startup. It validates `log_target`, `log_format`, `debug`, `log_privacy_mode`, `add_result_header`, `socket` format, and all per-check option names and values.

**SIGHUP** reloads the config file at runtime (`kill -HUP $PID` or `systemctl reload`). Only per-message settings take effect immediately (check options, exclusion lists, dry_run, enabled). Settings applied at startup only (`log_target`, `log_format`, `socket`, syslog settings, `log_filepath`) require a full restart.

## Test structure

- `tests/test-NN.lua` — functional miltertest scripts. Each starts the milter with a specific config (e.g., `tests/config.yaml` or `tests/test-NN-config.yaml`), sends a crafted SMTP session, and asserts the expected SMTP reply code.
- `tests/config.yaml` — default config used by most tests (dry_run=0 for all checks except a few).
- `tests/config-dry.yaml` — config with dry_run=1 globally, used by `*-dry.lua` tests.
- `tests/test-NN-config.yaml` — per-test config overrides (for exclusion list tests, test 81–99).
- `tests/config_syntax/` — YAML files for `--configcheck` syntax validation tests.
- `tests/01 overview of tests.txt` — human-readable index mapping test numbers to what they cover.
