import argparse

from linkarchivetools import Db2Feeds, DbFilter


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

    tmp_db = "tmp.db"

    filter = DbFilter(input_db = args.db, output_db = tmp_db)
    filter.filter_votes()

    analyzer = Db2Feeds(input_db = tmp_db, output_db=args.output_db)
    analyzer.convert()


main()
