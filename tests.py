import unittest

import anicli_ru as anicli


class TestRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.anime = anicli.Anime()

    def test_get_ongoings(self):
        """Test get ongoings list"""
        ongoings = self.anime.get_ongoing()
        self.assertIsInstance(ongoings, list)
        self.assertGreater(len(ongoings), 0)

    def test_search_1(self):
        """Test get anime list"""
        results = self.anime.search("Вайолет")
        self.assertEqual(len(results), 4)

    def test_search_2(self):
        """Test get banned title in Russia Federation"""
        self.anime.search("Эльфийская песнь")  # title, who have bigger than 1 episode and banned in Russia
        episodes = self.anime.parse_episodes_count(0)
        self.assertEqual(episodes, 13)
        self.anime.parse_series()
        self.assertEqual(len(self.anime._episodes), 0)

    def test_search_3(self):
        """Test normal case search and get episode"""
        self.anime.search("Джо")  # Jo'Jo Adventure
        episodes = self.anime.parse_episodes_count(5)  # chapter 1
        self.assertEqual(episodes, 26)
        self.anime.parse_series()
        choose = self.anime.choose_episode(0)
        self.assertEqual(choose[0]["dub"], "AniDUB")
        self.assertTrue("sibnet" in choose[0]["player"][0])  # sibnet player available

    def test_search_4(self):
        """Test get ongoing series"""
        ongoings = self.anime.get_ongoing()
        if len(ongoings) > 0:
            episodes_count = self.anime.parse_episodes_count(1)
            self.assertIsInstance(episodes_count, int)
            self.anime.parse_series()
            self.assertGreater(len(self.anime._episodes), 0)
        else:
            self.skipTest("Cannot get ongoings in your country or ip address")

    def test_search_5(self):
        """Test get anime episodes, but they have only an unsupported kodik player :( """
        self.anime.search("lain")  # experiments lain
        episodes = self.anime.parse_episodes_count(0)
        self.assertEqual(episodes, 13)
        self.anime.parse_series()
        choose = self.anime.choose_episode(12)
        self.assertIsInstance(choose, list)
        self.assertEqual(len(choose), 0)
