from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# Browser setup
s = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=s)
# driver.maximize_window()

driver.get("https://www.decisionproblem.com/paperclips/index2.html")

elem = driver.find_element(By.ID,"btnMakePaperclip")

# FIXME: The site doesn't contain the progress from a previous or manual session. It's completely clean.
for x in range(10):
    elem.click()

time.sleep(1)
driver.close()


# TODO
# Done: Launch a browser to correct web page
# Setup basic loop
# Read contents
# Parse contents


