from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
from Util.GameLoop.Strategizer import Strategizer
from Webpage.PageInfo import PageInfo
from Webpage.PageActions import PageActions

from multiprocessing.dummy import Pool as ThreadPool

config = dict(line.split("=")
              for line in open("Private/Config.txt").read().splitlines())

# Browser setup
s = Service(ChromeDriverManager().install())


options = webdriver.ChromeOptions()
options.add_argument(f'--user-data-dir={config["profilePath"]}')
options.add_argument(f'--profile-directory={config["profileDir"]}')

driver = webdriver.Chrome(service=s, chrome_options=options)
driver.get(config["webPage"])

driver.execute_script("reset()")  # Fresh start
driver.execute_script("save()")  # Page only saves periodically

print("\n\n\n**************************************************")

pInfo = PageInfo(driver)
pActions = PageActions(driver)
strat = Strategizer(pInfo, pActions)

running = True
while running:
    running = strat.tick()
print("Main loop aborted")

time.sleep(1)  # Watch in awe at your creation

driver.close()
