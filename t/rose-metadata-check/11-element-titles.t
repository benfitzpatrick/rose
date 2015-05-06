#!/bin/bash
#-------------------------------------------------------------------------------
# (C) British Crown Copyright 2012-5 Met Office.
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
# Test "rose metadata-check" for element-titles.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header
#-------------------------------------------------------------------------------
tests 9
#-------------------------------------------------------------------------------
# Check element titles syntax checking.
TEST_KEY=$TEST_KEY_BASE-syntax-ok
setup
init <<__META_CONFIG__
[namelist:nl1=colour]
element-titles=red,blue

[namelist:nl2=colour]
element-titles=red

[namelist:nl1=colour]
element-titles='red,reddish',blue
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check element-titles syntax checking.
TEST_KEY=$TEST_KEY_BASE-length-ok
setup
init <<__META_CONFIG__
[namelist:nl1=colour]
length=3
element-titles=Red,Blue,Green

[namelist:nl2=colour]
length=1
element-titles=Red

[namelist:nl3=colour]
length=:
element-titles=Red,Blue,Green

[namelist:nl4=black_sheep]
element-titles=Baa,Baa,Bags Full
type=character,character,integer

[namelist:nl5=black_sheeps]
element-titles=Baa,Baa,Bags Full
length=2
type=character,character,integer
__META_CONFIG__
run_pass "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
teardown
#-------------------------------------------------------------------------------
# Check value-titles syntax checking (fail).
TEST_KEY=$TEST_KEY_BASE-titles-bad
setup
init <<__META_CONFIG__
[namelist:nl1=colour]
length=3
element-titles=Red,Blue,Green,Orange

[namelist:nl2=colour]
length=1
element-titles=Red,Green

[namelist:nl4=black_sheep]
element-titles=Baaaaa
type=character,character,integer

[namelist:nl5=black_sheeps]
element-titles=Baa,Baa
length=2
type=character,character,integer
__META_CONFIG__
run_fail "$TEST_KEY" rose metadata-check -C ../config
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" <<__ERROR__
[V] rose.metadata_check.MetadataChecker: issues: 4
    namelist:nl1=colour=element-titles=Red,Blue,Green,Orange
        Incompatible with length
    namelist:nl2=colour=element-titles=Red,Green
        Incompatible with length
    namelist:nl4=black_sheep=element-titles=Baaaaa
        Incompatible with type
    namelist:nl5=black_sheeps=element-titles=Baa,Baa
        Incompatible with type
__ERROR__
teardown
#-------------------------------------------------------------------------------
exit
