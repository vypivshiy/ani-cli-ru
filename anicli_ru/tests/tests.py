import unittest
import requests

from anicli_ru.extractors.animego import ResultList, Ongoing, AnimeResult, Episode, Anime
from anicli_ru.extractors.animania import Anime as Anime2
from anicli_ru.extractors.animania import Ongoing as Ongoing2
from anicli_ru.extractors.animania import Episode as Episode2
from anicli_ru.extractors.animania import ResultList as ListObj2


class TestRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.anime = Anime()

    def test_get_ongoings(self):
        """Test get ongoings list"""
        ongoings = self.anime.ongoing()
        self.assertIsInstance(ongoings, ResultList)
        self.assertGreater(len(ongoings), 0)

    def test_search_1(self):
        """Test get anime list"""
        results = self.anime.search("Violet Evergarden")
        self.assertEqual(len(results), 4)
        self.assertIsInstance(results, ResultList)

    def test_search_2(self):
        """Test get banned title in Russia Federation"""
        results = self.anime.search("Elfen Lied")  # title, who have bigger than 1 episode and banned in Russia
        episodes = results[0].episodes()
        self.assertEqual(len(episodes), 0)

    def test_search_3(self):
        """Test normal case search and get episode"""
        results = self.anime.search("Angel Beats")
        episodes = results[1].episodes()
        self.assertEqual(len(episodes), 13)
        players = episodes[0].player()
        self.assertEqual(players[3].dub_name, "AniDUB")
        self.assertTrue("sibnet" in players[3].url)  # sibnet player available

    def test_search_4(self):
        """Test get ongoing series"""
        ongoings = self.anime.ongoing()
        self.assertGreater(len(ongoings), 0)
        if len(ongoings) > 0:
            episodes = ongoings[0].episodes()
            self.assertGreater(len(episodes), 0)
        else:
            self.skipTest("Cannot get ongoings in your country or ip address")

    def test_search_6(self):
        """Test get anime with kodik player"""
        results = self.anime.search("lain")  # experiments lain
        episodes = results[0].episodes()
        self.assertEqual(len(episodes), 13)
        players = episodes[12].player()
        self.assertIsInstance(players, ResultList)
        self.assertEqual(len(players), 1)

    def test_parser_ongoings(self):
        r = requests.get("https://animego.org").text
        ongoings = Ongoing.parse(r)
        self.assertIsInstance(ongoings, ResultList)
        self.assertGreater(len(ongoings), 0)

    def test_parser_anime(self):
        r = requests.get("https://animego.org/search/anime", params={"q": "lain"}).text
        rez = AnimeResult.parse(r)
        self.assertIsInstance(rez, ResultList)
        self.assertEqual(len(rez), 1)
        self.assertEqual(rez[0].id, '1114')

    def test_parser_episodes(self):
        r = requests.get("https://animego.org/anime/1114/player?_allow=true", headers={
            'x-requested-with': 'XMLHttpRequest'}).json()["content"]
        rez = Episode.parse(r)
        self.assertIsInstance(rez, ResultList)
        self.assertEqual(len(rez), 13)
        print()


class TestAnime2(unittest.TestCase):
    """test animania source"""

    @classmethod
    def setUpClass(cls) -> None:
        cls.anime = Anime2()

    def test_search(self):
        res = self.anime.search("experiments lain")
        self.assertEqual(len(res), 1)
        episodes = res[0].episodes()
        self.assertEqual(len(episodes), 1)
        players = episodes[0].player()
        self.assertEqual(len(players), 13)

    def test_parser1(self):
        r = requests.get("https://animania.online/index.php")
        ongoings = Ongoing2.parse(r.text)
        self.assertGreater(len(ongoings), 1)

    def test_parser2(self):
        r = requests.get("https://animania.online/9403-jeksperimenty-ljejn-serial-experiments-lain-1998-smotret-onlajn.html")
        res: ListObj2[Episode2] = Episode2.parse(r.text)
        self.assertEqual(len(res), 1)  # get XL Media dub
        players = res[0].player()
        self.assertEqual(len(players), 13)  # get 13 episodes
