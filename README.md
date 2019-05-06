# WritingInteractDownloader
a simple python script to download interactive stories from writing.com


Requirements
===============================================================

- Python 3.7
- requests
- lxml 

Example usage
===============================================================
```
python downloader.py https://www.writing.com/main/interact/item_id/178902-Awakenings-Journey-to-Iceland
```

this will download the whole story into a subdirectory consisting of the Id and the name of the story.
href links are replaced, so you can simply open the begin.html file in browser to start browsing the story.
