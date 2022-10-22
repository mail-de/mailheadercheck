#!/bin/bash

for testcase in tests/test-*.lua; do
	miltertest -s $testcase
done

exit 0
