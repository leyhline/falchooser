"""
Module for querying and committing to a database.
Creates mapping via SQLAlchemy's ORM.

Created on Apr 1, 2017

:copyright: (c) 2017 by Thomas Leyh.
:licence: GPLv3, see LICENSE for more details.
"""

from configparser import ConfigParser
import os

from sqlalchemy import Column, ForeignKey, create_engine, Table
from sqlalchemy import Integer, Float, DateTime, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship


CONFIG = ConfigParser()
CONFIG.read(os.path.join(os.path.expanduser("~"), ".falchooser.ini"))
try:
    DBENGINE = CONFIG["DEFAULT"]["DBEngine"]
except KeyError as e:
    raise e


Base = declarative_base()


user_anime_team = Table("user_anime_team", Base.metadata,
                        Column("users", ForeignKey("user.id"), primary_key=True),
                        Column("anime", ForeignKey("anime.id"), primary_key=True))


class Anime(Base):
    """
    This table just holds the anime's title and id.
    """
    __tablename__ = "anime"
    id = Column(Integer, primary_key=True, autoincrement=False)
    title = Column(String(1024), nullable=False)
    url = Column(String(2048), nullable=False, unique=True)
    users = relationship("User", secondary=user_anime_team, back_populates="anime")

    def __repr__(self):
        return "<Anime(id={}, title={})>".format(self.id, self.title)


class Statistics(Base):
    """
    Save the statistics as a time series.
    """
    __tablename__ = "statistics"
    anime = Column(Integer, ForeignKey("anime.id"), primary_key=True, autoincrement=False)
    day = Column(Integer, primary_key=True, autoincrement=False)
    score = Column(Float)
    users = Column(Integer)
    ranked = Column(Integer)
    popularity = Column(Integer)
    members = Column(Integer)
    favorites = Column(Integer)
    watching = Column(Integer)
    completed = Column(Integer)
    onhold = Column(Integer)
    dropped = Column(Integer)
    plantowatch = Column(Integer)
    accessed = Column(DateTime(timezone=True), nullable=False)

    def __repr__(self):
        return "<Statistics(anime={}, day={}, accessed={})>".format(self.anime, self.day, self.accessed)


class User(Base):
    """
    Simple list of MAL usernames.
    """
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    name = Column(String(256), nullable=False, unique=True)
    anime = relationship("Anime", secondary=user_anime_team, back_populates="users")

    def __repr__(self):
        return "<User(id={}, name={})>".format(self.id, self.name)


class Database:
    """
    Simple database class for creating tables and
    getting the session object (for queryies and inserts).
    """
    def __init__(self, engine: str=DBENGINE, echo: bool=False):
        self.engine = create_engine(engine, echo=echo)
        self._sessionmaker = sessionmaker(bind=self.engine)

    def create_tables(self):
        global Base
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        global Base
        Base.metadata.drop_all(self.engine)

    def get_session(self) -> Session:
        return self._sessionmaker()
