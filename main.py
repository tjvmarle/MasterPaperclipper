import time
from Util.Files.Config import Config
from Util.GameLoop.Strategizer import Strategizer
from Util.Gamesave import Gamesave
from Webpage.Initialization.Startpage import Startpage
from Util.Timestamp import Timestamp as TS

# Launch the webpage and load/save options
webPage = Startpage()
game = Gamesave(webPage.getDriver())

# Rough overview of next actions:
# TODO: Write some more UTs

# Load game
# game.load(Config.get("savePathPhotonicPhase"))

Config.set("Gamestart", TS.now())
strat = Strategizer(webPage.getDriver())

startTime = Config.get("Gamestart")
frameStamp = Config.get("Gamestart")
frames = 0
totalFrames = 0
totalTicks = 0

TS.print("Start!")
while strat.tick():
    frames += 1
    runtime = TS.delta(frameStamp)
    if runtime > 5.0:  # Average fps per 5 seconds
        fps = frames / runtime
        # TS.print(f"fps: {fps:.2f}")

        totalFrames += fps
        totalTicks += 1

        frameStamp = TS.now()
        frames = 0

TS.print(f"Finished in {TS.deltaStr(startTime)}.")
TS.print(f"Averaged {totalFrames / totalTicks:.2f} fps.")

# game.save(Config.get("savePathPhotonicPhase"))

time.sleep(3)  # Watch in awe at your creation
webPage.getDriver().close()  # UGLY, but fine for now.
