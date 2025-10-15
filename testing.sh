#!/bin/bash

set -u

failed=0
total=0

# Colors for output
GREEN="\033[0;32m"
RESET="\033[0m"

# 1) Config syntax checks using --configcheck
for cfg in tests/config_syntax/*.yaml; do
    if [ ! -f "$cfg" ]; then
        continue
    fi

    # Determine expected result from comment '# result: valid' or '# result: invalid'
    expected=$(grep -m1 -E '^# *result: *(valid|invalid)' "$cfg" | sed -E 's/^# *result: *//')
    if [ -z "${expected:-}" ]; then
        echo "WARN: No '# result: valid|invalid' comment found in $cfg, defaulting to invalid"
        expected="invalid"
    fi

    # --configcheck
    total=$((total+1))
    echo -n "Config syntax check (--configcheck) for $cfg (expected: $expected) ... "
    out=$(./mailheadercheck --config "$cfg" --configcheck 2>&1)
    rc=$?
    if [ "$expected" = "valid" ]; then
        if [ $rc -eq 0 ] && ! echo "$out" | grep -q "^ERROR: "; then
            echo -e "${GREEN}Test successful${RESET}"
        else
            echo
            echo "ERROR: Expected success and no ERROR output for $cfg (--configcheck)"
            echo "$out"
            failed=$((failed+1))
        fi
    else
        if [ $rc -ne 0 ] && echo "$out" | grep -q "^ERROR: "; then
            echo -e "${GREEN}Test successful${RESET}"
        else
            echo
            echo "ERROR: Expected non-zero exit and ERROR output for $cfg (--configcheck)"
            echo "$out"
            failed=$((failed+1))
        fi
    fi
done

# 2) Run milter functional tests
# Require miltertest to be present
if ! command -v miltertest >/dev/null 2>&1; then
    echo "ERROR: 'miltertest' command not found; please install the 'miltertest' package via apt (or install 'opendkim-tools' because 'miltertest' was a part of that package in the past)."
    exit 1
fi
for testcase in tests/test-*.lua; do
    total=$((total+1))
    echo -n "Running $testcase ... "
    out=$(miltertest -s "$testcase" 2>&1)
    rc=$?
    if [ $rc -ne 0 ]; then
        echo
        echo "ERROR: miltertest exited with code $rc for $testcase"
        echo "$out"
        failed=$((failed+1))
    else
        echo -e "${GREEN}Test successful${RESET}"
    fi
done

if [ $failed -ne 0 ]; then
    echo
    echo "Test summary: $failed of $total tests failed (non-zero exit)."
    exit 1
else
    echo
    echo "Test summary: All $total tests passed."
    exit 0
fi
