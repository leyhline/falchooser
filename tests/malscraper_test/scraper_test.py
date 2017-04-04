"""
Created on Mar 31, 2017
"""

import unittest
from numbers import Number
import falchooser.malscraper.scraper as scraper
from falchooser.malscraper.scraper import MalEntry


class Test(unittest.TestCase):


    def test_read_titles_without_ignore(self):
        titles = scraper.read_titles(2017, 2)
        self.assertEqual(titles[0], "Alice to Zouroku", "Titles do not match.")
        self.assertEqual(len(titles), 17, "Wrong length of title list.")

    def test_read_titles_with_ignore(self):
        titles = scraper.read_titles(2017, 2, True)
        self.assertEqual(len(titles), 27, "Wrong length of title list.")
        self.assertEqual(titles[0], "Berserk (2017)", "Titles do not match.")

    def test_search_an_anime(self):
        title = "Full Metal"
        mal = scraper.Mal()
        results = mal.search(title)
        self.assertGreater(len(results), 1, "Search should have more than 1 result.")
        self.assertEqual(results[0], (71, "Full Metal Panic!"))

    def test_get_url(self):
        mal = scraper.Mal()
        url = mal.get_url(34561)
        self.assertEqual(url, "https://myanimelist.net/anime/34561/Re_Creators")

    def test_parse_stats_of_entry(self):
        malentry = scraper.MalEntry("https://myanimelist.net/anime/33089/Kemono_Friends",
                                    33089)
        stats = malentry.get_stats()
        self.assertEqual(len(stats), 11)
        for value in stats.values():
            self.assertIsInstance(value, Number)
            self.assertLess(value, 2000000)

    def test_entry_constructor(self):
        malentry = scraper.MalEntry("https://myanimelist.net/anime/33089/Kemono_Friends")
        self.assertEqual(malentry.id, 33089)
        self.assertEqual(malentry.get_title(), "Kemono Friends")


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
