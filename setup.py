from setuptools import setup, find_packages


setup(
    name="falchooser",
    version="0.1",
    description="This program should help choosing a team for MyAnimeList's FAL.",
    url="https://github.com/leyhline/falchooser",
    author="Thomas Leyh",
    licence="GPLv3",
    packages=find_packages(exclude=["tests.*"]),
    install_requires=["lxml", "psycopg2", "SQLAlchemy", "requests", "cssselect"],
    package_data={
        "falchooser":["titles/*.txt"],
    },
    entry_points={
        "console_scripts": [
            "anime2db=falchooser.malscraper:cmd_stats_insert",
        ],
    },
)
