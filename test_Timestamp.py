from datetime import datetime
from Util.Timestamp import Timestamp as TS
import time
import datetime

now = TS.now()
future = now + datetime.timedelta(12, 7*3600 + 23*60 + 54)

print(now.second)

print(TS.deltaStr(now))
