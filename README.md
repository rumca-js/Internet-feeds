# Internet-feeds

This is a database of Internet feeds. Just unzip <b>feeds.zip</b>!

The archive contains a SQLite database, generated from various curated link collections (e.g. the [https://github.com/rumca-js/Internet-Places-Database](https://github.com/rumca-js/Internet-Places-Database) project).

You can open the database with any SQLite tool.

# Data

```
Table: linkdatamodel, Row count: 2645
```

## Access via web interface

```
unpack feeds.zip
python3 -m http.server 8000          # start server
https://localhost:8000/search.html   # visit
```
