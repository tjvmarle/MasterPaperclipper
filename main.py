import cProfile
import time
from Util.Files.Config import Config
from Util.GameLoop.PhaseRunner import PhaseRunner
from Util.GameLoop.Phases.CurrentPhase import CurrentPhase, Phase
from Util.Gamesave import Gamesave
from Webpage.Initialization.Startpage import Startpage
from Util.Timestamp import Timestamp as TS
from colorama import Fore, Style

# Launch the webpage and load/save options
webPage = Startpage()
game = Gamesave(webPage.getDriver())

# Load a previous save
# game.load(Config.get("savePathSecondPhase"))
# game.load(Config.get("savePathThirdPhase"))

Config.set("Gamestart", TS.now())
runner = PhaseRunner(webPage.getDriver())

startTime = Config.get("Gamestart")
frameStamp = Config.get("Gamestart")
frames = 0
totalFrames = 0
totalTicks = 0

TS.print("\n" * 10)
TS.print("Start!")


def loop():
    global totalFrames
    global totalTicks
    global frames
    global frameStamp
    while CurrentPhase.phase != Phase.End:
        runner.tick()

        frames += 1
        runtime = TS.delta(frameStamp)

        if runtime > 5.0:  # Average fps per 5 seconds
            fps = frames / runtime
            # TS.print(f"fps: {fps:.2f}")

            totalFrames += fps
            totalTicks += 1

            frameStamp = TS.now()
            frames = 0


loop()
# cProfile.run('loop()')
# OPT: Almost 100% of the time spent in webdriver.py:404(execute). On a per-call basis, all calls to the driver take about 13-14 ms, ~74 calls/s. Fewer calls == higher fps!

TS.print(f"{Fore.GREEN}Finished in {TS.deltaStr(startTime)}.{Style.RESET_ALL}")

if totalTicks > 0:
    TS.print(f"Averaged {totalFrames / totalTicks:.2f} fps.")

# time.sleep(15)
# webPage.getDriver().execute_script("save()")
# time.sleep(1)
# game.save(Config.get("savePathSecondPhase"))

time.sleep(3)  # Watch in awe at your creation
webPage.getDriver().close()  # UGLY, but fine for now.
