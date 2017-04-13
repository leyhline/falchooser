"""
Helper functions for using this module.

Created on Apr 2, 2017

:copyright: (c) 2017 by Thomas Leyh.
:licence: GPLv3, see LICENSE for more details.
"""

import datetime
import argparse
from typing import Sequence

from .scraper import read_titles, MalEntry, read_teamlist
from .dbaccess import Statistics, Anime, Database, User, Base


START_OF_DATA_COLLECTION = datetime.date(2017, 4, 2)


def create_stats_object(malentry: MalEntry) -> Statistics:
    """
    Create statistics database object (ORM) from MalEntry object.
    :param malentry: Use this as source of data.
    :return: Statistics object from SQLAlchemy's ORM.
    """
    malstats = malentry.get_stats()
    assert len(malstats) == 11, "There must be 11 statistic entries (current: {}).".format(len(malstats))
    now = datetime.datetime.now(datetime.timezone.utc)
    days = now.date() - START_OF_DATA_COLLECTION
    stats = Statistics(anime=malentry.id,
                                day=days.days,
                                score=malstats["score"],
                                users=malstats["users"],
                                ranked=malstats["ranked"],
                                popularity=malstats["popularity"],
                                members=malstats["members"],
                                favorites=malstats["favorites"],
                                watching=malstats["watching"],
                                completed=malstats["completed"],
                                onhold=malstats["onhold"],
                                dropped=malstats["dropped"],
                                plantowatch=malstats["plantowatch"],
                                accessed=now)
    return stats


def create_anime_object(malentry: MalEntry) -> Anime:
    """
    Create a Anime database object (ORM) form a MalEntry object.
    :param malentry: Use this as source of data.
    :return: Anime object from SQLAlchemy's ORM.
    """
    anime = Anime(id=malentry.id,
                           title=malentry.get_title(),
                           url=malentry.url)
    return anime


def db_insert(rows: Sequence[Base], y: bool) -> None:
    """
    Insert all given rows to database.
    :param rows: A list of database row objects.
    :param y: Omit confirmation dialog and default to y(es).
    """
    if not y:
        for row in rows:
            print(row)
        confirm = input("Confirm insertion of these rows (y/n): ")
    else:
        confirm = "y"
    if confirm == "y":
        db = Database()
        session = db.get_session()
        session.add_all(rows)
        session.commit()
        session.close()
    else:
        print("Insertion in database aborted.")


def insert_anime(year: int, quarter: int, ignored: bool=False, y: bool=False) -> None:
    """
    Insert all anime from specified season into database.
    Needs a file YYYY-Q-urls.txt in titles folder.
    Needs user input to confirm inserts if y is False.
    :param year: Year of broadcast.
    :param quarter: Quarter of broadcast (winter, spring, summer, fall).
    :param ignored: Read the titles from the 'ignored' file.
    :param y: Omit confirmation dialog and default to y(es).
    """
    urls = read_titles(year, quarter, ignored, True)
    entries = map(MalEntry, urls)
    animes = list(map(create_anime_object, entries))
    assert len(animes) == len(urls), ("Number of objects ({})".format(len(animes)),
            "and lines in titles file ({}) does not match.".format(len(urls)))
    db_insert(animes, y)


def insert_statistics(year: int, quarter: int, ignored: bool=False, y: bool=False) -> None:
    """
    Insert statistics for all specified anime at current date.
    Needs a file YYYY-Q-urls.txt in titles folder.
    Needs user input to confirm inserts if y is False.
    :param year: Year of broadcast.
    :param quarter: Quarter of broadcast (winter, spring, summer, fall).
    :param ignored: Read the titles from the 'ignored' file.
    :param y: Omit confirmation dialog and default to y(es).
    """
    urls = read_titles(year, quarter, ignored, True)
    entries = map(MalEntry, urls)
    stats = list(map(create_stats_object, entries))
    assert len(stats) == len(urls), ("Number of objects ({})".format(len(stats)),
            "and lines in titles file ({}) does not match.".format(len(urls)))
    db_insert(stats, y)


def insert_teamlist(filepath: str) -> None:
    """
    Insert users and teams into database.
    :param filepath: Path to teamlist-seasonYY.txt
    """
    teams = read_teamlist(filepath)
    db = Database()
    session = db.get_session()
    for username in teams:
        user = User(name=username)
        for anime in teams[username]:
            user.anime.append(session.query(Anime).filter(Anime.title==anime).first())
    session.commit()
    session.close()


def cmd_stats_insert() -> None:
    """
    Automatically scrape statistics and insert them into database.
    Control via command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Scrape anime statistics from MAL and insert them into database.")
    parser.add_argument("year", type=int, help="Year of broadcast.")
    parser.add_argument("quarter", type=int, help="Quarter of broadcast.", choices=[1, 2, 3, 4])
    parser.add_argument("-y", action="store_true", help="Omit confirmation dialog.")
    args = parser.parse_args()
    year = args.year
    quarter = args.quarter
    y = args.y
    print("Inserting statistics for {}-{}...".format(year, quarter))
    insert_statistics(year, quarter, False, y)
    print("Inserting statistics for {}-{}-ignore...".format(year, quarter))
    insert_statistics(year, quarter, True, y)
    print("Done.")
