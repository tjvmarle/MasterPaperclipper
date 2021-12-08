from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from Util.Files.Config import Config


class Startpage():
    def __init__(self) -> None:

        Config.load("Data/Private/Config.txt")
        Config.load("Data/Public/Config.txt")
        Config.loadProjects("Data/Public/PhaseOneProjects.csv")

        # Update the driver
        s = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument(f'--user-data-dir={Config.get("profilePath")}')
        options.add_argument(f'--profile-directory={Config.get("profileDir")}')

        # Start the webPage
        self.driver = webdriver.Chrome(service=s, chrome_options=options)
        self.driver.get(Config.get("webPage"))

        # Create a fresh start
        self.driver.execute_script("reset()")
        self.driver.execute_script("save()")
        pass

    def getDriver(self) -> webdriver.Chrome:
        return self.driver
