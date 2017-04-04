"""
Scraping some anime statistics from Mal for analyzing the FAL.

Created on Mar 31, 2017

:copyright: (c) 2017 by Thomas Leyh.
:licence: GPLv3, see LICENSE for more details.
"""

from configparser import ConfigParser
import os
from typing import Sequence, Tuple, Mapping, Union
from time import sleep
import re
from enum import Enum

import requests
from lxml import etree
import lxml.html


CONFIG = ConfigParser()
CONFIG.read(os.path.join(os.path.expanduser("~"), ".falchooser.ini"))
try:
    USERNAME = CONFIG["DEFAULT"]["Username"]
    PASSWORD = CONFIG["DEFAULT"]["Password"]
except KeyError as e:
    raise e


class ReType(Enum):
    COMMA = re.compile(r"""\d+(,\d+)*""")
    HASH = re.compile(r"""(?<=#)\d+""")
    DOT = re.compile(r"""\d.\d+""")
    USERS = re.compile(r"""\d+(,\d+)*(?= users)""")


def safe_requests_get(*args, **kwargs) -> requests.Request:
    """
    Make a safe request with error handling and retries.
    :param *args: These are passed to the requests.get function.
    :return: A request object with status code 200.
    """
    tried = 0
    while True:
        r = requests.get(*args, **kwargs)
        if r.status_code == 200:
            break
        elif tried >= 3:
            raise requests.HTTPError("{} - {}".format(r.status_code, r.text))
        else:
            print("{} - {}".format(r.status_code, r.text), "Trying again.")
            tried += 1
            sleep(1)  # Wait  for retry
    return r

def get_titles_path() -> str:
    """
    :return: Absulute path of titles textfiles.
    """
    path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.split(path)[0]
    return os.path.join(path, "titles")


def read_titles(year: int, quarter: int,
                ignored: bool=False, urls: bool=False) -> Sequence[str]:
    """
    Read textfile with anime titles and return them.
    :param year: Year of broadcast.
    :param quarter: Quarter of broadcast (winter, spring, summer, fall).
    :param ignored: Read the titles from the 'ignored' file.
    :param urls: Do not read titles but anime urls.
    :return: Sequence of anime titles.
    """
    ignore = "-ignore" if ignored else ""
    url = "-urls" if urls else ""
    path = get_titles_path()
    path = os.path.join(path, "{}-{}{}{}.txt".format(year, quarter, ignore, url))
    with open(path) as fd:
        return [line.strip() for line in fd if not line.isspace()]


class Mal:
    """
    Class for getting some anime's statistics from Mal.
    """
    URL = "https://myanimelist.net"

    def search(self, title: str) -> Sequence[Tuple[int, str]]:
        """
        Search for an anime.
        :param title: Title of the anime to search for.
        :return: A sequence of ordered search results with (id, title) tuples.
        """
        r = safe_requests_get(self.URL + "/api/anime/search.xml",
                              params={"q":title}, auth=(USERNAME, PASSWORD))
        root = etree.fromstring(r.content)
        entries = (child for child in root if child.tag == "entry")
        results = ((int(child.find("id").text), child.find("title").text)
                   for child in entries)
        return tuple(results)

    def get_url(self, id: int) -> str:
        """
        Create a Mal url from an anime's id.
        :param id: Mal id of a specific anime.
        :return: Absolute URL of an anime.
        """
        simple_url = self.URL + "/anime/" + str(id)
        r = safe_requests_get(simple_url)
        if r.status_code == 200:
            root = lxml.html.fromstring(r.content)
        else:
            raise requests.HTTPError("{} - {}".format(r.status_code, r.text))
        hnav = root.cssselect("a.horiznav_active")[0]
        url = hnav.attrib["href"]
        return url

    def write_urls(self, year: int, quarter: int,
                   ignored: bool=False) -> None:
        """
        Write urls of given animes to a file in titles path.
        Output file format is year-quarter-urls.txt.
        :param year: Specifies year of input file.
        :param quarter: Specifies year of input file.
        :param ignored: Get urls of ignored animes.
        """
        titles = read_titles(year, quarter, ignored)
        path = get_titles_path()
        ignore = "-ignore" if ignored else ""
        path = os.path.join(path, "{}-{}{}-urls.txt".format(year, quarter, ignore))
        urls = map(self._search_and_build_url, titles)
        with open(path, "x") as fd:
            for url in urls:
                fd.write(url + "\n")

    def _search_and_build_url(self, title: str) -> str:
        """
        Search for an anime title and return its Mal url.
        :param title: Search for this title.
        :return: Returns an url string or an empty string if nothing is found.
        """
        print("Searching for Title \"{}\".".format(title))
        results = self.search(title)
        result = tuple(result[0] for result in results if result[1] == title)
        if len(result) > 0:
            result = result[0]
        elif len(results) == 0:
            return ""
        else:
            result = results[0][0]
        return self.get_url(result)


class MalEntry:
    """
    Class for parsing the statistics of an anime on Mal.
    """
    re_id = re.compile(r"""(?<=anime/)\d+(?=/)""")
    re_na = re.compile(r"""N/A""")

    def __init__(self, url: str, id: int=None):
        """
        Constructor
        :param url: Absolute url of Mal entry.
        :param id: Id of entry or None.
        """
        self.url = url
        if id:
            self.id = id
        else:
            self.id = int(self.re_id.search(url).group())
        self.stats = dict()
        self._title = None

    def get_title(self) -> str:
        if not self._title:
            self._title = self._parse_title()
        return self._title

    def _parse_title(self) -> str:
        r = safe_requests_get(self.url)
        root = lxml.html.fromstring(r.content)
        title = root.cssselect("h1.h1")[0]
        return title[0].text

    def get_stats(self) -> Mapping[str, Union[int, str]]:
        """
        Returns statistics of this entry. If these got already parsed
        it just returns the stats attribute.
        :return: Dictionary of different statistics.
        """
        if not self.stats:
            self.parse_stats()
        return self.stats

    def parse_stats(self) -> None:
        """
        Make a request to parse some statistics.
        """
        r = safe_requests_get(self.url + "/stats")
        root = lxml.html.fromstring(r.content)
        # Get statistics from left border.
        lborder = root.cssselect("div.js-scrollfix-bottom")[0]
        divs = [child for child in lborder if child.tag == "div"]
        # Get statistics from central body.
        cbody = root.cssselect("div.js-scrollfix-bottom-rel")[0]
        rows = cbody.cssselect("div.spaceit_pad")
        divs.extend(rows)
        for div in divs:
            mapping = self._parse_mapping(div)
            if mapping:
                self.stats.update(mapping)

    def _parse_mapping(self, div_element: lxml.html.HtmlElement):
        children = div_element.getchildren()
        if len(children) > 0:
            key = children[0].text
        else:
            return None
        mapping = dict()
        if key == "Score:":
            mapping["score"] = self._match_and_convert(div_element, ReType.DOT)
            mapping["users"] = self._match_and_convert(div_element, ReType.USERS)
        elif key == "Ranked:":
            mapping["ranked"] = self._match_and_convert(div_element, ReType.HASH)
        elif key == "Popularity:":
            mapping["popularity"] = self._match_and_convert(div_element, ReType.HASH)
        elif key == "Members:":
            mapping["members"] = self._match_and_convert(div_element, ReType.COMMA)
        elif key == "Favorites:":
            mapping["favorites"] = self._match_and_convert(div_element, ReType.COMMA)
        elif key == "Watching:":
            mapping["watching"] = self._match_and_convert(div_element, ReType.COMMA)
        elif key == "Completed:":
            mapping["completed"] = self._match_and_convert(div_element, ReType.COMMA)
        elif key == "On-Hold:":
            mapping["onhold"] = self._match_and_convert(div_element, ReType.COMMA)
        elif key == "Dropped:":
            mapping["dropped"] = self._match_and_convert(div_element, ReType.COMMA)
        elif key == "Plan to Watch:":
            mapping["plantowatch"] = self._match_and_convert(div_element, ReType.COMMA)
        else:
            return None
        return mapping

    def _match_and_convert(self, div_element: lxml.html.HtmlElement,
                           re_type: ReType) -> int:
        # Remove sup elements because they fuck the parsing up.
        sups = div_element.findall("sup")
        for sup in sups:
            div_element.remove(sup)
        value = div_element.text_content()
        # Check if the entry is "N/A" and return None if yes.
        if re_type.name != "USERS" and self.re_na.search(value):
            return None
        value = re_type.value.search(value).group()
        if re_type.name == "DOT":
            return float(value)
        elif re_type.name == "COMMA" or "USERS":
            value = value.replace(",","")
        return int(value)
