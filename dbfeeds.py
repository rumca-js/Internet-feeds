import os
import json
import argparse
from pathlib import Path
from sqlalchemy import create_engine
from concurrent.futures import ThreadPoolExecutor, as_completed

from linkarchivetools import (
   Db2Feeds,
   DbFilter,
   DbMerge,
)
from linkarchivetools.utils.reflected import ReflectedEntryTable
from webtoolkit import (
   OpmlPage,
   BaseUrl,
   RssPage,
   ContentLinkParser,
)
from webtoolkitex import UrlEx
import webtoolkitex


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
    request = webtoolkitex.webconfig.WebConfig.get_default_request(feed)
    request.timeout_s = 70
    url = UrlEx(url=feed, request=request)
    response = url.get_response()
    return feed, url


def get_feed_properties(feed, url):
    """
    Returns feed properties
    """
    result = {}
    properties = url.get_properties()
    response = url.get_response()

    # not null requirement
    result["source_url"] = ""
    result["permanent"] = False
    result["bookmarked"] = False
    result["contents_type"] = 0
    result["page_rating_contents"] = 0
    result["page_rating_visits"] = 0
    result["page_rating_votes"] = 0
    result["page_rating"] = 0

    result["link"] = feed
    result["title"] = url.get_title()
    result["description"] = url.get_description()
    result["thumbnail"] = url.get_thumbnail()
    result["language"] = url.get_language()
    result["author"] = url.get_author()
    result["status_code"] = url.get_status_code()

    result["manual_status_code"] = 0
    if "page_rating_contents" in properties:
        result["page_rating_contents"] = properties["page_rating_contents"]

    return result

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


def filter_feeds(table, all_feeds):
    result = set()

    for feed in all_feeds:
        print(f"Checking {feed}")
        url = UrlEx(url=feed)
        new_feeds = url.get_feeds()
        if len(new_feeds) > 0:
            feed = new_feeds[0]

        if not table.is_entry_link(feed):
            result.add(feed)
    return result


def process_feeds(db_name, all_feeds):
    print("Filtering feeds")
    engine = create_engine(f"sqlite:///{db_name}")
    with engine.connect() as connection:
        table = ReflectedEntryTable(engine, connection)
        used_feeds = filter_feeds(table, all_feeds)

    used_feeds = list(used_feeds)

    print("Fetching")
    batch_size = 100
    total_size = len(used_feeds)
    for loop_base in range(0, total_size, batch_size):
       print(f"New loop {loop_base}")
       engine = create_engine(f"sqlite:///{db_name}")
       with engine.connect() as connection:
          table = ReflectedEntryTable(engine, connection)

          batch_feeds = used_feeds[loop_base:loop_base + batch_size]

          with ThreadPoolExecutor(max_workers=5) as executor:  # run 5 at a time
             futures = []
             process_feeds_executor(batch_feeds, executor, futures, table, total_size, batch_size, loop_base)


def process_feeds_executor(feeds, executor, futures, table, total_size, batch_size, loop_base):
    """
    Process all feeds
    """
    for feed in feeds:
        futures.append(executor.submit(fetch_feed, feed))

    total = total_size
    completed = loop_base

    for future in as_completed(futures):
        completed += 1
        remaining = total - completed

        feed, url = future.result()

        text = f"[{completed}/{total}] {feed}:"

        if type(url.get_response().get_page()) is RssPage:
            print(text + "OK")
            properties = get_feed_properties(feed, url)
            if "link" in properties and properties["link"]:
                new_entry_id = table.insert_json_data("linkdatamodel", properties)
        else:
            print(text + "NOK")


def read_link_database_sources():
    """
    Returns sources from JSON
    """
    feeds = set()

    url = UrlEx("https://raw.githubusercontent.com/rumca-js/RSS-Link-Database/refs/heads/main/sources.json")
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

    parser = ContentLinkParser(url="https://raw.githubusercontent.com/wokenlex/infobubble-support/refs/heads/main/Sources/all.sources.rss.yaml", contents=text)
    links = parser.get_links()

    for link in links:
        feeds.add(link)

    return feeds


def parse():
    parser = argparse.ArgumentParser(description="Data analyzer program")
    parser.add_argument("--db", default="places.db", help="DB to be scanned")
    parser.add_argument("--output-db", default="feeds.db", help="DB to be produced")
    parser.add_argument("--remote-server", help="DB to be scanned")

    parser.add_argument("--convert", action="store_true", help="DB to be scanned")
    parser.add_argument("--add-lists", action="store_true", help="DB to be scanned")
    parser.add_argument("--update", action="store_true", help="DB to be scanned")
    parser.add_argument("--merge", action="store_true", help="DB to be scanned")

    parser.add_argument("--merge-db", default="feeds_merge.db", help="DB to be scanned")
    parser.add_argument("--old-feeds-db", default="feeds_old.db", help="old feeds DB")

    args = parser.parse_args()

    return parser, args


def convert(args):
    tmp_db = "tmp.db"

    print(f"Filtering {args.db} entries")

    filter = DbFilter(input_db = args.db, output_db = tmp_db)
    filter.filter_votes()

    print(f"{args.db} places -> feeds")

    converter = Db2Feeds(input_db = tmp_db, output_db=args.output_db, read_internet_links=True, remote_server=args.remote_server)
    converter.convert()


def add_lists(args):
    """
    Can be called on preexisting database, will try to add new entries
    """
    all_feeds = set()

    awesome_path = Path("awesome-rss-feeds-master")
    if awesome_path.exists():
        print("Reading awesome RSS feeds")
        all_feeds.update(get_all_opml_feeds(args, "awesome-rss-feeds-master"))

    print("Reading rumca-js feeds")
    all_feeds.update(read_link_database_sources())
    print("Reading infobuble feeds")
    all_feeds.update(read_infobubble_sources())

    print("I have {} feeds".format(len(all_feeds)))
    print("Processing feeds")
    process_feeds(args.output_db, all_feeds)
    print("Processing feeds DONE")


def merge(args):
    """
    move feeds.db -> feeds.old.db
    convert(args)
    merge feeds.old.db + feeds.db -> output.db
    """
    input_db1 = args.old_feeds_db
    input_db2 = args.merge_db
    output_db = args.output_db

    input_dbs = [input_db1, input_db2]

    merge = DbMerge(input_dbs=input_dbs, output_db=output_db)
    merge.convert()


def update(args):
    """
    Updates status_code of entries
    """

def main():
    parser, args = parse()
    if not args.db:
        print("Please specify database")
        return

    if args.convert:
        convert(args)

    if args.add_lists:
        add_lists(args)

    if args.merge:
        merge(args)

    if args.update:
        update(args)


main()
