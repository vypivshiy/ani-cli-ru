import unittest

from anicli_ru import Anime, ListObj


class TestRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.anime = Anime()

    def test_get_ongoings(self):
        """Test get ongoings list"""
        ongoings = self.anime.ongoing()
        self.assertIsInstance(ongoings, ListObj)
        self.assertGreater(len(ongoings), 0)

    def test_search_1(self):
        """Test get anime list"""
        results = self.anime.search("Violet Evergarden")
        self.assertEqual(len(results), 4)
        self.assertIsInstance(results, ListObj)

    def test_search_2(self):
        """Test get banned title in Russia Federation"""
        results = self.anime.search("Эльфийская песнь")  # title, who have bigger than 1 episode and banned in Russia
        episodes = self.anime.episodes(results[0])
        self.assertEqual(len(episodes), 0)

    def test_search_3(self):
        """Test normal case search and get episode"""
        results = self.anime.search("Джо")  # Jo'Jo Adventures
        episodes = results.choose(6).episodes()  # chapter 1
        self.assertEqual(len(episodes), 26)
        choose = episodes[0]
        players = choose.player()
        self.assertEqual(players[0].dub_name, "AniDUB")
        self.assertTrue("sibnet" in players[0].url)  # sibnet player available

    def test_search_4(self):
        """Test get ongoing series"""
        ongoings = self.anime.ongoing()
        self.assertGreater(len(ongoings), 0)
        if len(ongoings) > 0:
            episodes = self.anime.episodes(ongoings.choose(1))
            self.assertIsInstance(episodes, ListObj)
            self.assertGreater(len(episodes), 0)
        else:
            self.skipTest("Cannot get ongoings in your country or ip address")

    def test_search_5(self):
        """Test get anime episodes, but they have only an unsupported kodik player :( """
        results = self.anime.search("lain")  # experiments lain
        episodes = results[0].episodes()
        self.assertEqual(len(episodes), 13)
        players = episodes[12].player()
        self.assertIsInstance(players, ListObj)
        self.assertEqual(len(players), 0)

