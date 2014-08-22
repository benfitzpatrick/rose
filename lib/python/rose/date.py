# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
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
#-----------------------------------------------------------------------------
"""Parse and format date and time."""

from datetime import datetime
from isodatetime.data import Calendar, Duration, get_timepoint_for_now
from isodatetime.dumpers import TimePointDumper
from isodatetime.parsers import TimePointParser, DurationParser
import os
import re
from rose.env import UnboundEnvironmentVariableError
from rose.opt_parse import RoseOptionParser
from rose.reporter import Reporter
import sys


class OffsetValueError(ValueError):

    """Bad offset value."""

    def __str__(self):
        return "%s: bad offset value" % self.args[0]


class RoseDateTimeOperator(object):

    """A class to parse and print date string with an offset."""

    CURRENT_TIME_DUMP_FORMAT = u"CCYY-MM-DDThh:mm:ss+hh:mm"
    CURRENT_TIME_DUMP_FORMAT_Z = u"CCYY-MM-DDThh:mm:ssZ"

    NEGATIVE = "-"

    # strptime formats and their compatibility with the ISO 8601 parser.
    PARSE_FORMATS = [
        ("%a %b %d %H:%M:%S %Y", True),     # ctime
        ("%a %b %d %H:%M:%S %Z %Y", True),  # Unix "date"
        ("%Y-%m-%dT%H:%M:%S", False),       # ISO8601, extended
        ("%Y%m%dT%H%M%S", False),           # ISO8601, basic
        ("%Y%m%d%H", False)                 # Cylc (current)
    ]

    REC_OFFSET = re.compile(r"""\A[\+\-]?(?:\d+[wdhms])+\Z""", re.I)

    REC_OFFSET_FIND = re.compile(r"""(?P<num>\d+)(?P<unit>[wdhms])""")

    STR_NOW = "now"
    STR_REF = "ref"

    TASK_CYCLE_TIME_MODE_ENV = "ROSE_TASK_CYCLE_TIME"

    UNITS = {"w": "weeks",
             "d": "days",
             "h": "hours",
             "m": "minutes",
             "s": "seconds"}

    def __init__(self, parse_format=None, utc_mode=False, calendar_mode=None,
                 ref_time_point=None):
        """Constructor.

        parse_format -- If specified, parse with the specified format.
                        Otherwise, parse with one of the format strings in
                        self.PARSE_FORMATS. The format should be a string
                        compatible to strptime(3).

        utc_mode -- If True, parse/print in UTC mode rather than local or
                    other timezones.

        calendar_mode -- Set calendar mode, for isodatetime.data.Calendar.

        ref_time_point -- Set the reference time point for operations.
                          If not specified, operations use current date time.

        """
        self.parse_formats = self.PARSE_FORMATS
        self.custom_parse_format = parse_format
        self.utc_mode = utc_mode
        if self.utc_mode:
            assumed_time_zone = (0, 0)
        else:
            assumed_time_zone = None

        if not calendar_mode:
            calendar_mode = os.getenv("ROSE_CYCLING_MODE")

        if calendar_mode and calendar_mode.lower() in Calendar.MODES:
            Calendar.default().set_mode(calendar_mode)

        self.time_point_dumper = TimePointDumper()
        self.time_point_parser = TimePointParser(
            assumed_time_zone=assumed_time_zone)
        self.duration_parser = DurationParser()

        self.ref_time_point = ref_time_point

    def date_format(self, print_format, time_point=None):
        """Reformat time_point according to print_format.

        time_point -- The time point to format.
                      Otherwise, use current date time.

        """
        if print_format is None:
            return str(time_point)
        if "%" in print_format:
            try:
                return time_point.strftime(print_format)
            except ValueError:
                return self.get_datetime_strftime(time_point, print_format)
        return self.time_point_dumper.dump(time_point, print_format)

    def date_parse(self, time_point_str=None):
        """Parse time_point_str.

        Return (t, format) where t is a isodatetime.data.TimePoint object and
        format is the format that matches time_point_str.

        time_point_str -- The time point string to parse.
                          Otherwise, use current time.

        """
        if time_point_str is None or time_point_str == self.STR_REF:
            time_point_str = self.ref_time_point
        if time_point_str is None or time_point_str == self.STR_NOW:
            time_point = get_timepoint_for_now()
            time_point.set_time_zone_to_local()
            if self.utc_mode or time_point.get_time_zone_utc():  # is in UTC
                parse_format = self.CURRENT_TIME_DUMP_FORMAT_Z
            else:
                parse_format = self.CURRENT_TIME_DUMP_FORMAT
        elif self.custom_parse_format is not None:
            parse_format = self.custom_parse_format
            time_point = self.strptime(time_point_str, parse_format)
        else:
            parse_formats = list(self.parse_formats)
            time_point = None
            while parse_formats:
                parse_format, should_use_datetime = parse_formats.pop(0)
                try:
                    if should_use_datetime:
                        time_point = self.get_datetime_strptime(
                            time_point_str,
                            parse_format)
                    else:
                        time_point = self.time_point_parser.strptime(
                            time_point_str,
                            parse_format)
                    break
                except ValueError:
                    pass
            if time_point is None:
                time_point = self.time_point_parser.parse(
                    time_point_str,
                    dump_as_parsed=True)
                parse_format = None
        if self.utc_mode:
            time_point.set_time_zone_to_utc()
        return time_point, parse_format

    def date_shift(self, time_point=None, offset=None):
        """Return a date string with an offset.

        time_point -- A time point or time point string.
                      Otherwise, use current time.

        offset -- If specified, it should be a string containing the offset
                  that has the format "[+/-]nU[nU...]" where "n" is an
                  integer, and U is a unit matching a key in self.UNITS.

        """
        if time_point is None:
            time_point = self.date_parse()[0]
        # Offset
        if offset:
            sign = "+"
            if offset.startswith("-") or offset.startswith("+"):
                sign = offset[0]
                offset = offset[1:]
            if offset.startswith("P"):
                # Parse and apply.
                try:
                    duration = self.duration_parser.parse(offset)
                except ValueError:
                    raise OffsetValueError(offset)
                if sign == "-":
                    time_point -= duration
                else:
                    time_point += duration
            else:
                # Backwards compatibility for e.g. "-1h"
                if not self.is_offset(offset):
                    raise OffsetValueError(offset)
                for num, unit in self.REC_OFFSET_FIND.findall(offset.lower()):
                    num = int(num)
                    if sign == "-":
                        num = -num
                    key = self.UNITS[unit]
                    time_point += Duration(**{key: num})

        return time_point

    def date_diff(self, time_point_1=None, time_point_2=None):
        """Return (duration, is_negative) between two TimePoint objects.

        duration -- is a Duration instance.
        is_negative -- is a RoseDateTimeOperator.NEGATIVE if time_point_2 is
                       in the past of time_point_1.
        """
        if time_point_2 < time_point_1:
            return (time_point_1 - time_point_2, self.NEGATIVE)
        else:
            return (time_point_2 - time_point_1, "")

    @classmethod
    def date_diff_format(cls, print_format, duration, sign):
        """Format a duration."""
        if print_format:
            delta_lookup = {"y": duration.years,
                            "m": duration.months,
                            "d": duration.days,
                            "h": duration.hours,
                            "M": duration.minutes,
                            "s": duration.seconds}
            expression = ""
            for item in print_format:
                if item in delta_lookup:
                    expression += str(delta_lookup[item])
                else:
                    expression += item
            return sign + expression
        else:
            return sign + str(duration)

    def is_offset(self, offset):
        """Return True if the string offset can be parsed as an offset."""
        return (self.REC_OFFSET.match(offset) is not None)

    def strftime(self, time_point, print_format):
        """Use either the isodatetime or datetime strftime time formatting."""
        try:
            return time_point.strftime(print_format)
        except ValueError:
            return self.get_datetime_strftime(time_point, print_format)

    def strptime(self, time_point_str, parse_format):
        """Use either the isodatetime or datetime strptime time parsing."""
        try:
            return self.time_point_parser.strptime(time_point_str,
                                                   parse_format)
        except ValueError:
            return self.get_datetime_strptime(time_point_str, parse_format)

    @classmethod
    def get_datetime_strftime(cls, time_point, print_format):
        """Use the datetime library's strftime as a fallback."""
        calendar_date = time_point.copy().to_calendar_date()
        year, month, day = calendar_date.get_calendar_date()
        hour, minute, second = time_point.get_hour_minute_second()
        microsecond = int(1.0e6 * (second - int(second)))
        hour = int(hour)
        minute = int(minute)
        second = int(second)
        date_time = datetime(year, month, day, hour, minute, second,
                             microsecond)
        return date_time.strftime(print_format)

    def get_datetime_strptime(self, time_point_str, parse_format):
        """Use the datetime library's strptime as a fallback."""
        date_time = datetime.strptime(time_point_str, parse_format)
        return self.time_point_parser.parse(date_time.isoformat())


def main():
    """Implement "rose date"."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options(
        "calendar",
        "diff",
        "offsets1",
        "offsets2",
        "parse_format",
        "print_format",
        "task_cycle_time_mode",
        "utc_mode")
    opts, args = opt_parser.parse_args()
    report = Reporter(opts.verbosity - opts.quietness)

    ref_time_point = None
    if opts.task_cycle_time_mode:
        ref_time_point = os.getenv(
            RoseDateTimeOperator.TASK_CYCLE_TIME_MODE_ENV)
        if ref_time_point is None:
            exc = UnboundEnvironmentVariableError(
                RoseDateTimeOperator.TASK_CYCLE_TIME_MODE_ENV)
            report(exc)
            if opts.debug_mode:
                raise exc
            sys.exit(1)

    date_time_oper = RoseDateTimeOperator(
        parse_format=opts.parse_format,
        utc_mode=opts.utc_mode,
        calendar_mode=opts.calendar,
        ref_time_point=ref_time_point)

    try:
        if len(args) < 2:
            _print_time_point(date_time_oper, opts, args)
        else:
            _print_duration(date_time_oper, opts, args)
    except OffsetValueError as exc:
        report(exc)
        if opts.debug_mode:
            raise exc
        sys.exit(1)


def _print_time_point(date_time_oper, opts, args):
    """Implement usage 1 of "rose date", print time point."""

    time_point_str = None
    if args:
        time_point_str = args[0]
    time_point, parse_format = date_time_oper.date_parse(time_point_str)
    if opts.offsets1:
        for offset in opts.offsets1:
            time_point = date_time_oper.date_shift(time_point, offset)
    if opts.print_format:
        print date_time_oper.date_format(opts.print_format, time_point)
    elif parse_format:
        print date_time_oper.date_format(parse_format, time_point)
    else:
        print str(time_point)


def _print_duration(date_time_oper, opts, args):
    """Implement usage 2 of "rose date", print duration."""
    time_point_str_1, time_point_str_2 = args
    time_point_1 = date_time_oper.date_parse(time_point_str_1)[0]
    time_point_2 = date_time_oper.date_parse(time_point_str_2)[0]
    if opts.offsets1:
        for offset in opts.offsets1:
            time_point_1 = date_time_oper.date_shift(time_point_1, offset)
    if opts.offsets2:
        for offset in opts.offsets2:
            time_point_2 = date_time_oper.date_shift(time_point_2, offset)
    duration, sign = date_time_oper.date_diff(time_point_1, time_point_2)
    print date_time_oper.date_diff_format(opts.print_format, duration, sign)


if __name__ == "__main__":
    main()
