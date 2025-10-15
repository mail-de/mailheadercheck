#!/bin/bash

set -u

failed=0
total=0

for testcase in tests/test-*.lua; do
    total=$((total+1))
    echo "Running $testcase ..."
    miltertest -s "$testcase"
    rc=$?
    if [ $rc -ne 0 ]; then
        echo "ERROR: miltertest exited with code $rc for $testcase"
        failed=$((failed+1))
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
