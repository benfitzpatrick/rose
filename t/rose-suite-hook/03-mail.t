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
# Test "rose suite-hook --mail", without site/user configurations.
#-------------------------------------------------------------------------------
. $(dirname $0)/test_header

python -m smtpd -c DebuggingServer -d -n 1>smtpd.out 2>&1 &
SMTPD_PID=$!
while ! grep -q 'DebuggingServer started' smtpd.out 2>/dev/null; do
    if ps $SMTPD_PID 1>/dev/null 2>&1; then
        sleep 1
    else
        skip_all "$TEST_KEY_BASE: cannot start SMTP server"
    fi
done
mkdir conf
cat >conf/rose.conf <<'__CONF__'
[rose-suite-hook]
smtp-host=localhost:8025
__CONF__
export ROSE_CONF_PATH=$PWD/conf

#-------------------------------------------------------------------------------
tests 26
#-------------------------------------------------------------------------------
# Run the suite.
SUITE_RUN_DIR=$(mktemp -d --tmpdir=$HOME/cylc-run 'rose-test-battery.XXXXXX')
NAME=$(basename $SUITE_RUN_DIR)
rose suite-run -C $TEST_SOURCE_DIR/$TEST_KEY_BASE --name=$NAME \
    --no-gcontrol --host=localhost -q -- --debug
N_QUIT=0
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE
run_pass "$TEST_KEY" rose suite-hook --mail succeeded $NAME t1.1 ''
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
((++N_QUIT))
TIMEOUT=$(($(date +%s) + 10))
while (($(date +%s) <= $TIMEOUT)) \
    && (($(grep -c "Data: 'quit'" smtpd.out) < $N_QUIT))
do
    sleep 1
done
tail -2 smtpd.out >smtpd-tail.out
file_grep "$TEST_KEY.smtp.from" "From: $USER@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" "To: $USER@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.subject" \
    "Subject: \\[succeeded\\] $NAME" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.1" "Task: t1.1" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.2" "See: file://$SUITE_RUN_DIR" smtpd-tail.out
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-cc
run_pass "$TEST_KEY" \
    rose suite-hook --mail --mail-cc=holly,ivy succeeded $NAME t1.1 ''
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
((++N_QUIT))
TIMEOUT=$(($(date +%s) + 10))
while (($(date +%s) <= $TIMEOUT)) \
    && (($(grep -c "Data: 'quit'" smtpd.out) < $N_QUIT))
do
    sleep 1
done
tail -2 smtpd.out >smtpd-tail.out
file_grep "$TEST_KEY.smtp.from" "From: $USER@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" "To: $USER@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" \
    "Cc: holly@localhost, ivy@localhost" smtpd-tail.out
file_grep "$TEST_KEY.smtp.subject" \
    "Subject: \\[succeeded\\] $NAME" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.1" "Task: t1.1" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.2" "See: file://$SUITE_RUN_DIR" smtpd-tail.out
#-------------------------------------------------------------------------------
TEST_KEY=$TEST_KEY_BASE-at-host
cat >conf/rose.conf <<'__CONF__'
[rose-suite-hook]
smtp-host=localhost:8025
email-host=hms.beagle
__CONF__
run_pass "$TEST_KEY" rose suite-hook \
    --mail --mail-cc=robert.fitzroy,charles.darwin succeeded $NAME t1.1 ''
file_cmp "$TEST_KEY.out" "$TEST_KEY.out" </dev/null
file_cmp "$TEST_KEY.err" "$TEST_KEY.err" </dev/null
((++N_QUIT))
TIMEOUT=$(($(date +%s) + 10))
while (($(date +%s) <= $TIMEOUT)) \
    && (($(grep -c "Data: 'quit'" smtpd.out) < $N_QUIT))
do
    sleep 1
done
tail -2 smtpd.out >smtpd-tail.out
file_grep "$TEST_KEY.smtp.from" "From: $USER@" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" "To: $USER@hms.beagle" smtpd-tail.out
file_grep "$TEST_KEY.smtp.to" \
    "Cc: robert.fitzroy@hms.beagle, charles.darwin@hms.beagle" smtpd-tail.out
file_grep "$TEST_KEY.smtp.subject" \
    "Subject: \\[succeeded\\] $NAME" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.1" "Task: t1.1" smtpd-tail.out
file_grep "$TEST_KEY.smtp.content.2" "See: file://$SUITE_RUN_DIR" smtpd-tail.out
#-------------------------------------------------------------------------------
rose suite-clean -q -y $NAME
kill $SMTPD_PID
wait $SMTPD_PID 2>/dev/null || true
exit 0
