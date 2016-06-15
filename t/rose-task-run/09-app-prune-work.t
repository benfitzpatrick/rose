#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-6 Met Office.
#
# This file is part of Rose, a framework for meteorological suites.
#
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
#-------------------------------------------------------------------------------
# Test "rose_prune" built-in application, more advanced usage on work directory.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

#-------------------------------------------------------------------------------
tests 2
#-------------------------------------------------------------------------------
export ROSE_CONF_PATH=
TEST_KEY=$TEST_KEY_BASE
mkdir -p $HOME/cylc-run
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
run_pass "$TEST_KEY" \
    rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -- --debug
#-------------------------------------------------------------------------------
TEST_KEY="$TEST_KEY_BASE-prune.log"
datetime_replace "${SUITE_RUN_DIR}/prune.log" > stamp-removed.log
cat stamp-removed.log >/dev/tty
echo "DONE STAMP REMOVED LOG" >/dev/tty
echo >/dev/tty
echo >/dev/tty
sed '/^\[INFO\] YYYY-MM-DDT... export ROSE_TASK_CYCLE_TIME=/p;
    /^\[INFO\] YYYY-MM-DDT... delete: /!d' \
    stamp-removed.log >edited-prune.log
cat "$TEST_SOURCE_DIR/$TEST_KEY_BASE.log" >/dev/tty
echo >/dev/tty
echo >/dev/tty
echo >/dev/tty
echo >/dev/tty
cat edited-prune.log >/dev/tty
file_cmp "$TEST_KEY" "$TEST_SOURCE_DIR/$TEST_KEY_BASE.log" edited-prune.log
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
exit 0
