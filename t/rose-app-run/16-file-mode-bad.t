#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-4 Met Office.
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
# Test "rose app-run", file installation, bad mode value.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 3
#-------------------------------------------------------------------------------
test_init <<'__CONFIG__'
[command]
default=true

[file:COPYING]
source=$ROSE_HOME/COPYING
# Oops, typos
mode=5ym1ink
__CONFIG__
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
test_setup
run_fail "$TEST_KEY" rose app-run --config=../config -q
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<'__ERR__'
[FAIL] file:COPYING=mode=5ym1ink: bad setting
__ERR__
test_teardown
#-------------------------------------------------------------------------------
exit
