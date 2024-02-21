#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Program entry point"""

from __future__ import print_function

import argparse
import csv
from datetime import datetime, UTC
import os.path
import sys
import time
from configparser import RawConfigParser

import feedparser
import requests
from dotenv import load_dotenv

from dstifbot import metadata

load_dotenv()


class ConfigLogger(object):
    def __init__(self, log):
        self.__log = log

    def __call__(self, config):
        self.__log.info("Config:")
        config.write(self)

    def write(self, data):
        line = data.strip()
        self.__log.info(line)


def send_api(content: str, title: str, url: str, date_published: str) -> int:
    if not date_published:
        date_published = datetime.now(UTC)
    else:
        date_published = int(date_published) * 1000
    response = requests.post(
        url=os.getenv("API_ENDPOINT"),
        headers={
            "Content-Type": "application/json",
            "X-MicrofeedAPI-Key": os.getenv("API_KEY"),
        },
        json={
            "title": title,
            "status": "published",
            "content_html": content,
            "url": url + "?utm_source=dstif.io",
            "date_published_ms": date_published
        },
    )

    debug = False
    if debug:
        print(response.request.url)
        print(response.request.headers)
        print(response.request.body)
        print(response.status_code)

    return response.status_code


def emoji(feed):
    # Nice emoji :)
    match feed:
        case "Leak-Lookup":
            title = '💧 '
        case "VERSION":
            title = '🔥 '
        case "DataBreaches":
            title = '🕳 '
        case "FR-CERT Alertes" | "FR-CERT Avis":
            title = '🇫🇷 '
        case "EU-ENISA Publications":
            title = '🇪🇺 '
        case "Cyber-News":
            title = '🕵🏻‍♂️ '
        case "Bleeping Computer":
            title = '💻 '
        case "Microsoft Sentinel":
            title = '🔭 '
        case "Hacker News":
            title = '📰 '
        case "Cisco":
            title = '📡 '
        case "Securelist":
            title = '📜 '
        case "ATT":
            title = '📞 '
        case "Google TAG":
            title = '🔬 '
        case "DaVinci Forensics":
            title = '📐 '
        case "VirusBulletin":
            title = '🦠 '
        case "Information Security Magazine":
            title = '🗞 '
        case "US-CERT CISA":
            title = '🇺🇸 '
        case "NCSC":
            title = '🇬🇧 '
        case "SANS":
            title = '🌍 '
        case "malpedia":
            title = '📖 '
        case "Unit42":
            title = '🚓 '
        case "Microsoft Security":
            title = 'Ⓜ️ '
        case "Checkpoint Research":
            title = '🏁 '
        case "Proof Point":
            title = '🧾 '
        case "RedCanary":
            title = '🦆 '
        case "MSRC Security Update":
            title = '🚨 '
        case "CIRCL Luxembourg":
            title = '🇱🇺 '
        case _:
            title = '📢 '
    return title


def get_rss_from_url(rss_item, debug=False):
    file_config = RawConfigParser()
    try:
        file_config.read(os.path.abspath("config.txt"))
        # print({section: dict(file_config[section]) for section in file_config})
    except Exception as e:
        sys.exit(str(e))

    news_feed = feedparser.parse(rss_item[0])
    date_activity = ""
    is_initial_run = False

    for rss_object in reversed(news_feed.entries):
        try:
            date_activity = time.strftime(
                "%Y-%m-%dT%H:%M:%S", rss_object.published_parsed
            )
            millisec = time.strftime('%s', rss_object.published_parsed)
        except:
            date_activity = time.strftime(
                "%Y-%m-%dT%H:%M:%S", rss_object.updated_parsed
            )
            millisec = time.strftime('%s', rss_object.updated_parsed)

        try:
            '''
            if debug:
                logging.basicConfig(level=logging.INFO)
                config_logger = ConfigLogger(logging)
                config_logger(file_config)

                print(rss_item[1])
            '''
            tmp_object = file_config.get("Rss", rss_item[1])
        except:
            file_config.set("Rss", rss_item[1], " = ?")
            tmp_object = file_config.get("Rss", rss_item[1])

        if tmp_object.endswith("?"):
            file_config.set('Rss', rss_item[1], date_activity)
        else:
            if (tmp_object >= date_activity):
                continue

        # d = datetime.datetime(date_activity)
        output_message = "Date: " + date_activity
        output_message += "<br/>"
        # output_message += "Title:<b> " + rss_object.title + "</b>"
        # output_message += "<br/>"
        output_message += "Source:<b> " + rss_item[1] + "</b>"
        output_message += "<br/>"
        output_message += "Read more: <a href=" + rss_object.link + "?utm_source=yeetum.com>"
        output_message += rss_object.link + "?utm_source=dstif.io</a>"
        output_message += "<br/>"

        title = emoji(rss_item[1]) + " " + rss_object.title
        url = rss_object.link
        if debug:
            print(title)
            print(output_message)
        else:
            send_api(content=output_message, title=title, url=url, date_published=millisec)
        file_config.set('Rss', rss_item[1], date_activity)

    with open(os.path.abspath("config.txt"), 'w') as file_handle:
        file_config.write(file_handle)


def get_ransomware_updates(debug: bool = False):
    data = requests.get('https://data.ransomware.live/posts.json')
    for entries in data.json():
        date_activity = entries['discovered']



def create_log_string(rss_item):
    log_string = "[*]" + time.ctime() + " checked " + rss_item
    print(log_string)


def main(argv):
    """Program entry point.

    :param argv: command-line arguments
    :type argv: :class:`list`
    """
    author_strings = []
    for name, email in zip(metadata.authors, metadata.emails):
        author_strings.append("Author: {0} <{1}>".format(name, email))

    epilog = """
{project} {version}

{authors}
URL: <{url}>
""".format(
        project=metadata.project,
        version=metadata.version,
        authors="\n".join(author_strings),
        url=metadata.url,
    )

    arg_parser = argparse.ArgumentParser(
        prog=argv[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=metadata.description,
        epilog=epilog,
    )
    arg_parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="{0} {1}".format(metadata.project, metadata.version),
    )
    arg_parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        dest="quiet",
        default=False,
        help="Quiet mode",
    )
    arg_parser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        dest="debug",
        default=False,
        help="Debug mode : only output on screen nothing send to dstif.io",
    )
    arg_parser.add_argument(
        "-d",
        "--domain",
        action="store_true",
        default=False,
        help="Enable Red Flag Domains source",
    ),
    arg_parser.add_argument(
        "-r",
        "--reminder",
        action="store_true",
        dest="reminder",
        default=False,
        help="Enable monthly reminder of Feeds",
    )

    args = arg_parser.parse_args()

    print(epilog)
    if args.debug:
        print(args)

    configuration_file_path = os.path.abspath("config.txt")
    feed_file_path = os.path.abspath("feed.csv")

    if sys.version_info < (3, 10):
        sys.exit("Please use Python 3.10+")
    if str(configuration_file_path) == "None" and not args.debug:
        sys.exit("Please create the config.txt file")
    if str(feed_file_path) == "None" and not args.debug:
        sys.exit("Please create the feed.csv file")

    with open(feed_file_path, newline="") as file:
        reader = csv.reader(file)
        rss_feed_list = list(reader)

    for rss_item in rss_feed_list:
        if "#" in str(rss_feed_list[0]):
            continue
        get_rss_from_url(rss_item, args.debug)
        create_log_string(rss_item[1])

    get_ransomware_updates(args.debug)
    create_log_string('Ransomware List')
    return 0


def entry_point():
    """Zero-argument entry point for use with setuptools/distribute."""
    raise SystemExit(main(sys.argv))


if __name__ == "__main__":
    entry_point()
