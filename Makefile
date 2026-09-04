# Define variables
ARCHIVE_NAME = feeds.db.zip
SOURCE_FILE = feeds.db

# Declare phony targets
.PHONY: zip zip-only unzip clean server pack-split unpack-split example-search search-youtube merge update

# Rule to create a zip archive split into 50MB parts
zip:
	zip $(ARCHIVE_NAME) $(SOURCE_FILE)
	echo "Packed $(SOURCE_FILE) into $(ARCHIVE_NAME)"
	rm -f $(SOURCE_FILE)

unzip:
	[ -e $(SOURCE_FILE) ] && rm -r $(SOURCE_FILE) || true
	7z x $(ARCHIVE_NAME)

zip-only:
	zip $(ARCHIVE_NAME) $(SOURCE_FILE)
	echo "Packed $(SOURCE_FILE) into $(ARCHIVE_NAME)"
	rm -f $(SOURCE_FILE)

pack-split:
	zip $(ARCHIVE_NAME) $(SOURCE_FILE)
	split -b 50M -d $(ARCHIVE_NAME) $(ARCHIVE_NAME)
	echo "Packed $(SOURCE_FILE) into $(ARCHIVE_NAME) parts"
	rm -f $(SOURCE_FILE)
	rm -f $(ARCHIVE_NAME)

unpack-split:
	cat internet* > $(ARCHIVE_NAME)
	7z x $(ARCHIVE_NAME)
	rm -f $(ARCHIVE_NAME)

filter:
	poetry run python dbfeeds.py
	rm tmp.db

# Clean rule to remove the archive
clean:
	rm -f $(ARCHIVE_NAME)
	echo "Removed $(ARCHIVE_NAME)"

server:
	python3 -m http.server 8000

summary:
	poetry run python dbanalyzer.py --tables --db $(SOURCE_FILE)

example-search:
	poetry run python ./dbanalyzer.py --db feeds.db --search "*Warhammer*" --tags --social --title --description --status

search-youtube:
	#poetry run python ./dbanalyzer.py --db feeds.db --search "*youtube.com/channel*" --title --tags --social
	poetry run python ./dbanalyzer.py --db feeds.db --search "*videos.xml?channel*"

download-data:
	wget https://github.com/plenaryapp/awesome-rss-feeds/archive/refs/heads/master.zip
	7z x master.zip
	rm master.zip

merge:
	wget https://github.com/rumca-js/awesome-database-top/raw/refs/heads/main/internet.db.zip
	unzip internet.db.zip
	rm internet.db.zip
	mv feedsdb.db feeds.db #from backup
	poetry run python dbfeeds.py --convert --db internet.db --output-db converted.db
	poetry run python dbfeeds.py --merge --merge-db converted.db --old-feeds-db feeds.db --output-db feeds_new.db
	rm feeds.db
	mv feeds_new.db feeds.db
	rm converted.db
	rm internet.db
	rm tmp.db

# adds from awesome lists, etc.
# The lists fetch and add into table. Should we add 'jobs' only, though?
add-lists:
	poetry run python dbfeeds.py --add-lists --output-db feeds.db

# not necessary any more. Current feeds are updated by yafr instance
# update:
#	poetry run python dbfeeds.py --update --db feeds.db
