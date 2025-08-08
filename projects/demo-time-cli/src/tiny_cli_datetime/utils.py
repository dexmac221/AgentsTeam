import datetime
from typing import Optional, Union

__all__ = [
"format_datetime",
"format_date",
"format_time",
"parse_datetime",
"get_current_datetime",
"get_current_date",
"get_current_time",
"to_isoformat",
"from_isoformat",
]


def format_datetime(
dt: datetime.datetime, fmt: str = "%Y-%m-%d %H:%M:%S"
) -> str:
"""
Format a datetime object into a string using the provided format.

Parameters
----------
dt : datetime.datetime
The datetime instance to format.
fmt : str, optional
The format string following strftime conventions. Defaults to
"%Y-%m-%d %H:%M:%S".

Returns
-------
str
The formatted datetime string.
"""
if not isinstance(dt, datetime.datetime):
raise TypeError("dt must be a datetime.datetime instance")
return dt.strftime(fmt)


def format_date(dt: datetime.datetime, fmt: str = "%Y-%m-%d") -> str:
"""
Format a datetime object into a date string.

Parameters
----------
dt : datetime.datetime
The datetime instance to format.
fmt : str, optional
The format string following strftime conventions. Defaults to
"%Y-%m-%d".

Returns
-------
str
The formatted date string.
"""
if not isinstance(dt, datetime.datetime):
raise TypeError("dt must be a datetime.datetime instance")
return dt.strftime(fmt)


def format_time(dt: datetime.datetime, fmt: str = "%H:%M:%S") -> str:
"""
Format a datetime object into a time string.

Parameters
----------
dt : datetime.datetime
The datetime instance to format.
fmt : str, optional
The format string following strftime conventions. Defaults to
"%H:%M:%S".

Returns
-------
str
The formatted time string.
"""
if not isinstance(dt, datetime.datetime):
raise TypeError("dt must be a datetime.datetime instance")
return dt.strftime(fmt)


def parse_datetime(
s: str, fmt: str = "%Y-%m-%d %H:%M:%S"
) -> datetime.datetime:
"""
Parse a datetime string into a datetime object using the provided format.

Parameters
----------
s : str
The datetime string to parse.
fmt : str, optional
The format string following strptime conventions. Defaults to
"%Y-%m-%d %H:%M:%S".

Returns
-------
datetime.datetime
The parsed datetime object.
"""
if not isinstance(s, str):
raise TypeError("s must be a string")
try:
return datetime.datetime.strptime(s, fmt)
except ValueError as exc:
raise ValueError(f"String '{s}' does not match format '{fmt}'") from exc


def get_current_datetime(
tz: Optional[datetime.tzinfo] = None
) -> datetime.datetime:
"""
Return the current datetime, optionally localized to a timezone.

Parameters
----------
tz : datetime.tzinfo, optional
Timezone to apply. If None, returns naive datetime in local time.

Returns
-------
datetime.datetime
The current datetime.
"""
now = datetime.datetime.now(tz=tz)
return now


def get_current_date(tz: Optional[datetime.tzinfo] = None) -> datetime.date:
"""
Return the current date, optionally localized to a timezone.

Parameters
----------
tz : datetime.tzinfo, optional
Timezone to apply. If None, returns naive date in local time.

Returns
-------
datetime.date
The current date.
"""
return get_current_datetime(tz).date()


def get_current_time(tz: Optional[datetime.tzinfo] = None) -> datetime.time:
"""
Return the current time, optionally localized to a timezone.

Parameters
----------
tz : datetime.tzinfo, optional
Timezone to apply. If None, returns naive time in local time.

Returns
-------
datetime.time
The current time.
"""
return get_current_datetime(tz).time()


def to_isoformat(dt: Union[datetime.datetime, datetime.date, datetime.time]) -> str:
"""
Convert a datetime, date, or time object to its ISO 8601 string representation.

Parameters
----------
dt : datetime.datetime | datetime.date | datetime.time
The object to convert.

Returns
-------
str
ISO 8601 formatted string.
"""
if isinstance(dt, (datetime.datetime, datetime.date, datetime.time)):
return dt.isoformat()
raise TypeError("dt must be datetime, date, or time instance")


def from_isoformat(s: str, obj_type: type = datetime.datetime) -> Union[datetime.datetime, datetime.date, datetime.time]:
"""
Parse an ISO 8601 string into a datetime, date, or time object.

Parameters
----------
s : str
ISO 8601 formatted string.
obj_type : type, optional
The desired return type: datetime.datetime, datetime.date, or datetime.time.
Defaults to datetime.datetime.

Returns
-------
datetime.datetime | datetime.date | datetime.time
The parsed object.
"""
if not isinstance(s, str):
raise TypeError("s must be a string")
if obj_type is datetime.datetime:
return datetime.datetime.fromisoformat(s)
if obj_type is datetime.date:
return datetime.date.fromisoformat(s)
if obj_type is datetime.time:
return datetime.time.fromisoformat(s)
raise ValueError("obj_type must be datetime, date, or time")