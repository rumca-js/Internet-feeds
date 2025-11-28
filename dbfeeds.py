import argparse

from linkarchivetools.db2feeds import Db2Feeds


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

    analyzer = Db2Feeds(input_db = args.db, output_db=args.output_db)
    analyzer.process()


main()
