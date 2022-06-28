from datetime import datetime
from datetime import timedelta
from datetime import timezone


def class_log_printer(func):
    utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
    cn_now = utc_now.astimezone(timezone(timedelta(hours=8))).strftime("%m/%d/%Y, %H:%M:%S")

    def inner_func(self, *args, **kwargs):
        return_func_value = func(self, *args, **kwargs)
        print(cn_now + " " + str(return_func_value))
        return return_func_value

    return inner_func
