from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from Util.Files.Config import Config


class Startpage():
    """Sets up the basic configuration for the rest of the classes. Also holds the chromedriver."""

    def __init__(self, fresh: bool = True) -> None:

        Config.load("Data/Private/Config.txt")
        Config.load("Data/Public/Config.txt")
        Config.loadProjects("Data/Public/Projects.csv")

        # Update the driver
        s = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument(f'--user-data-dir={Config.get("profilePath")}')
        options.add_argument(f'--profile-directory={Config.get("profileDir")}')

        # Start the webPage
        self.driver = webdriver.Chrome(service=s, chrome_options=options)
        self.driver.get(Config.get("webPage"))

        if fresh:
            self.driver.execute_script("reset()")
            self.driver.execute_script("save()")

    def getDriver(self) -> webdriver.Chrome:
        # TODO: get rid of this.
        return self.driver
