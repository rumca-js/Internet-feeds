import os
import json
import argparse
from pathlib import Path
from sqlalchemy import create_engine
from concurrent.futures import ThreadPoolExecutor, as_completed

from linkarchivetools import Db2Feeds, DbFilter
from linkarchivetools.utils.reflected import ReflectedEntryTable
from webtoolkit import OpmlPage, BaseUrl, RssPage
from webtoolkitex import UrlEx


def list_files_recursive(root_dir):
    """
    List files recursively
    """
    file_paths = []
    for root, dirs, files in os.walk(root_dir):
        for filename in files:
            full_path = os.path.join(root, filename)
            file_paths.append(full_path)
    return file_paths


def fetch_feed(feed):
    """
    Fetch a feed
    """
    url = UrlEx(feed)
    response = url.get_response()
    return feed, url


def get_feed_properties(feed, url):
    """
    Returns feed properties
    """
    result = {}
    properties = url.get_properties()

    result["link"] = feed
    result["title"] = url.get_title()
    result["description"] = url.get_description()
    result["status_code"] = url.get_status_code()
    result["manual_status_code"] = 0

    # not null requirement
    result["source_url"] = ""
    result["permanent"] = False
    result["bookmarked"] = False
    result["contents_type"] = 0
    result["page_rating_contents"] = 0
    result["page_rating_visits"] = 0
    result["page_rating_votes"] = 0
    result["page_rating"] = 0

    return result


def process_feeds_executor(feeds, executor, futures, table):
    """
    Process all feeds
    """
    for feed in feeds:
        print("{} Fetching...".format(feed))

        url = UrlEx(url=feed)
        new_feeds = url.get_feeds()
        if len(new_feeds) > 0:
            feed = new_feeds[0]

        if not table.is_entry_link(feed):
            futures.append(executor.submit(fetch_feed, feed))

    for future in as_completed(futures):
        feed, url = future.result()
        if type(url.get_response().get_page()) is RssPage:
            print(f"{feed}:OK")
            properties = get_feed_properties(feed, url)
            if "link" in properties and properties["link"]:
                new_entry_id = table.insert_json_data("linkdatamodel", properties)
        else:
            print(f"{feed}:NOK")


def find_opml_files(root_directory):
    """
    Returns list of OPML files from directory
    """
    result = []
    all_files = list_files_recursive(root_directory)
    for file in all_files:
        if file.endswith("opml"):
            result.append(file)

    return result


def get_all_opml_feeds(args, directory):
    all_files = find_opml_files(directory)
    print("Found OPML {} files".format(len(all_files)))
    all_feeds = get_opml_feeds(all_files)
    print("Found OMPL {} feeds".format(len(all_feeds)))
    return all_feeds


def get_opml_feeds(all_files):
    """
    Get all feeds from all OPML files
    """
    result = set()
    for f in all_files:
        print("Processing file {}".format(f))
        with open(f, "r") as fh:
            data = fh.read()
            page = OpmlPage("", contents=data)
            feeds = set(page.get_feeds())
            for feed in feeds:
                result.add(feed)

    return result


def process_feeds(db_name, all_feeds):
    engine = create_engine(f"sqlite:///{db_name}")
    with engine.connect() as connection:
        table = ReflectedEntryTable(engine, connection)

        with ThreadPoolExecutor(max_workers=5) as executor:  # run 5 at a time
            futures = []

            process_feeds_executor(all_feeds, executor, futures, table)


def read_link_database_sources():
    """
    Returns sources from JSON
    """
    feeds = set()

    url = UrlEx("https://raw.githubusercontent.com/rumca-js/RSS-Link-Database-2025/refs/heads/main/sources.json")
    response = url.get_response()
    text = response.get_text()
    loaded = json.loads(text)

    for item in loaded:
        feeds.add(item["url"])

    return feeds


def read_infobubble_sources():
    """
    Returns sources from infobubble
    """
    feeds = set()

    url = UrlEx("https://raw.githubusercontent.com/wokenlex/infobubble-support/refs/heads/main/Sources/all.sources.rss.yaml")
    response = url.get_response()
    text = response.get_text()
    loaded = json.loads(text)

    for item in loaded:
        feeds.add(item["url"])

    return feeds


def parse():
    parser = argparse.ArgumentParser(description="Data analyzer program")
    parser.add_argument("--db", default="places.db", help="DB to be scanned")
    parser.add_argument("--output-db", default="feeds.db", help="DB to be scanned")

    args = parser.parse_args()

    return parser, args


def main():
    parser, args = parse()
    if not args.db:
        print("Please specify database")
        return

    # tmp_db = "tmp.db"

    print(f"Filtering {args.db} entries")

    filter = DbFilter(input_db = args.db, output_db = tmp_db)
    filter.filter_votes()

    print(f"{args.db} places -> feeds")

    analyzer = Db2Feeds(input_db = tmp_db, output_db=args.output_db)
    analyzer.convert()

    all_feeds = []

    awesome_path = Path("awesome-rss-feeds-master")
    if awesome_path.exists():
        print("Reading awesome RSS feeds")
        all_feeds.extend(get_all_opml_feeds(args, "awesome-rss-feeds-master"))


    print("Reading rumca-js feeds")
    all_feeds.extend(read_link_database_sources())

    print("I have {} feeds".format(len(all_feeds)))
    print("Processing feeds")
    process_feeds(args.output_db, all_feeds)
    print("Processing feeds DONE")


main()
