from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from Util.GameLoop.Strategizer import Strategizer
from Webpage.PageState.PageInfo import PageInfo
from Webpage.PageState.PageActions import PageActions
from Util.Timestamp import Timestamp as TS

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

TS.print(f"Finished in {TS.deltaStr(startTime)}.")
time.sleep(1)  # Watch in awe at your creation
driver.close()
