from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class Startpage():
    def __init__(self) -> None:
        config = dict(line.split("=") for line in open("Private/Config.txt").read().splitlines())
        s = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument(f'--user-data-dir={config["profilePath"]}')
        options.add_argument(f'--profile-directory={config["profileDir"]}')

        self.driver = webdriver.Chrome(service=s, chrome_options=options)
        self.driver.get(config["webPage"])

        self.driver.execute_script("reset()")  # Fresh start
        self.driver.execute_script("save()")  # Page only saves periodically
        pass

    def getDriver(self) -> webdriver.Chrome:
        return self.driver
