# Define variables
ARCHIVE_NAME = feeds.zip
SOURCE_FILE = feeds.db

# Declare phony targets
.PHONY: zip zip-only unzip clean server pack-split unpack-split example-search example-search2 merge update

# Rule to create a zip archive split into 50MB parts
zip:
	zip -s 50m $(ARCHIVE_NAME) $(SOURCE_FILE)
	echo "Packed $(SOURCE_FILE) into $(ARCHIVE_NAME)"
	rm -f $(SOURCE_FILE)
	rm tmp.db

unzip:
	[ -e $(SOURCE_FILE) ] && rm -r $(SOURCE_FILE) || true
	7z x $(ARCHIVE_NAME)

zip-only:
	zip -s 50m $(ARCHIVE_NAME) $(SOURCE_FILE)
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
	poetry run python dataanalyzer.py --summary --db $(SOURCE_FILE)

example-search:
	poetry run python ./dataanalyzer.py --db internet.db --search "*Warhammer*" --tags --social --title --description --status
example-search2:
	poetry run python ./dataanalyzer.py --db internet.db --search "*youtube.com/channel*" --title --tags --social

download-data:
	wget https://github.com/plenaryapp/awesome-rss-feeds/archive/refs/heads/master.zip
	7z x master.zip
	rm master.zip

merge:
	poetry run python dbfeeds.py --convert --db places.db --output-db converted.db
	poetry run python dbfeeds.py --merge --merge-db converted.db --old-feeds-db feeds.db --output-db feeds_new.db
	rm feeds.db
	mv feeds_new.db feeds.db

update:
	poetry run python dbfeeds.py --update --db feeds.db
