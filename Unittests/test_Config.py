import unittest
from Util.Files.Config import Config


class TestConfig(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Config.load("Unittests/TestData/TestConfig.txt")

    def test_regular_properties(self):
        self.assertEqual(Config.get("stuffingIt"), "closeTogether")
        self.assertEqual(Config.get("answer"), "42")
        self.assertEqual(Config.get("aGoodLasagna"), "hasLayers(andLayers(andLayers(andLayers(andLayers))))")

    def test_single_line_lists(self):
        self.assertEqual(Config.get("nrList"), ["1", "2", "3", "4", "5", "6"])
        self.assertEqual(Config.get("midlifeDwarves"), ["flabby", "baldy",
                                                        "alkie", "divorcy", "sleepy", "moresleepy", "moody"])

    def test_multi_line_lists(self):
        self.assertTrue("white rum," not in Config.get("Mojito"))
        self.assertTrue("," not in Config.get("Mojito"))
        self.assertEqual("white rum", Config.get("Mojito")[0])
        self.assertEqual("plenty of ice", Config.get("Mojito")[-1])


if __name__ == '__main__':
    unittest.main()
