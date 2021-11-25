import unittest
import requests

from anicli_ru import Anime
from anicli_ru.api import ListObj, Ongoing, AnimeResult, Episode, AnimeInfo


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
        self.assertEqual(players[2].dub_name, "AniDUB")
        self.assertTrue("sibnet" in players[2].url)  # sibnet player available

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

    def test_search_6(self):
        """Test get anime with kodik player"""
        results = self.anime.search("lain")  # experiments lain
        episodes = results[0].episodes()
        self.assertEqual(len(episodes), 13)
        players = episodes[12].player()
        self.assertIsInstance(players, ListObj)
        self.assertEqual(len(players), 1)

    def test_search_random(self):
        """Test get random anime title

        Maybe fail due to bans in your country"""
        result = self.anime.random()  # return ListObj with one element
        self.assertIsInstance(result, ListObj)
        eps = result[0].episodes()
        self.assertIsInstance(eps, ListObj)
        self.assertGreater(len(eps), 0)

    def test_parser_ongoings(self):
        r = requests.get("https://animego.org").text
        ongoings = Ongoing.parse(r)
        self.assertIsInstance(ongoings, ListObj)
        self.assertGreater(len(ongoings), 0)

    def test_parser_anime(self):
        r = requests.get("https://animego.org/search/anime", params={"q": "lain"}).text
        rez = AnimeResult.parse(r)
        self.assertIsInstance(rez, ListObj)
        self.assertEqual(len(rez), 1)
        self.assertEqual(rez[0].id, '1114')

    def test_parser_episodes(self):
        r = requests.get("https://animego.org/anime/1114/player?_allow=true", headers={
            'x-requested-with': 'XMLHttpRequest'}).json()["content"]
        rez = Episode.parse(r)
        self.assertIsInstance(rez, ListObj)
        self.assertEqual(len(rez), 13)
        print()

    def test_parser_detailed_info(self):
        r = self.anime.search("lain")[0]
        info = r.info()
        self.assertEqual(info.status, "Вышел")
        self.assertEqual(info.type, "ТВ Сериал")
        self.assertEqual(info.status, "Вышел")
        self.assertEqual(info.source, "Оригинал")
        self.assertEqual(info.title, "Эксперименты Лэйн")
