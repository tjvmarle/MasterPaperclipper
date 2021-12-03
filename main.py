from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from Util.GameLoop.Strategizer import Strategizer
from Webpage.PageInfo import PageInfo
from Webpage.PageActions import PageActions
from Util.Timestamp import Timestamp as TS

from multiprocessing.dummy import Pool as ThreadPool

config = dict(line.split("=")
              for line in open("Private/Config.txt").read().splitlines())

# TODO: Move initialization to seperate class
s = Service(ChromeDriverManager().install())
options = webdriver.ChromeOptions()
options.add_argument(f'--user-data-dir={config["profilePath"]}')
options.add_argument(f'--profile-directory={config["profileDir"]}')

driver = webdriver.Chrome(service=s, chrome_options=options)
driver.get(config["webPage"])

driver.execute_script("reset()")  # Fresh start
driver.execute_script("save()")  # Page only saves periodically

print("\n\n\n**************************************************\n\n\n")

pInfo = PageInfo(driver)
pActions = PageActions(driver)
strat = Strategizer(pInfo, pActions)

TS.print("Start!")
startTime = TS.now()

while strat.tick():
    pass

totalTime = TS.delta(startTime)

# TODO: Make this a function in TimeStamp. Can be useful to monitor other parts of the code.
timeString = ""
if totalTime > 3600:
    hours = int(totalTime / 3600)
    totalTime = totalTime - hours * 3600
    timeString += f"{hours} hour"
    if hours > 1:
        timeString += "s"

if totalTime > 60:
    if timeString:
        timeString += ", "

    minutes = int(totalTime / 60)
    totalTime = totalTime - minutes * 60
    timeString += f"{minutes} minute"

    if minutes > 1:
        timeString += "s"

if totalTime >= 1:
    if timeString:
        timeString += ", "

    timeString += f"{int(totalTime)} second"

    if totalTime > 1:
        timeString += "s"

TS.print(f"Finished in {timeString}.")
time.sleep(1)  # Watch in awe at your creation
driver.close()
