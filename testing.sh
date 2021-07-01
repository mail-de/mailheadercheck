#!/bin/bash

for testcase in tests/test-*; do
	miltertest -s $testcase
done

exit 0
