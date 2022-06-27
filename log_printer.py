from datetime import datetime
from datetime import timedelta
from datetime import timezone


def log_printer(func):
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    cn_now = utc_now.astimezone(timezone(timedelta(hours=8))).strftime("%m/%d/%Y, %H:%M:%S")

    def inner_func():
        return func()

    print(cn_now + " " + str(inner_func()))
    return inner_func
