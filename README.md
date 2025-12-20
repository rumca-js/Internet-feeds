# Internet-feeds

This is a database of Internet feeds. Just unzip <b>feeds.zip</b>!

The archive contains a SQLite database, generated from various curated link collections (e.g. the [https://github.com/rumca-js/Internet-Places-Database](https://github.com/rumca-js/Internet-Places-Database) project).

You can open the database with any SQLite tool.

# Data

```
Table: linkdatamodel, Row count: 3788
```

How can your page, or RSS feed enter this database? Well...

 - first it needs to be on the internet. Available, scrapable (title and stuff needs to be there)
 - it needs to wait, until it is picked up by scrapers
 - only feeds with a great amount of attention and recognition are part of this database

## Access via web interface

```
unpack feeds.zip
python3 -m http.server 8000          # start server
https://localhost:8000/search.html   # visit
```
