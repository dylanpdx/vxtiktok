from flask import Flask
from yt_dlp import YoutubeDL
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def findApiFormat(videoInfo):
    for format in videoInfo['formats']:
        if format['format_id'] == 'download_addr-0':
            return format['url']
    # not found, search for the next best one
    for format in videoInfo['formats']:
        if format['url'].startswith('http://api'):
            return format['url']
    # not found, return the first one
    return videoInfo['formats'][0]['url']
    return None

def getVideoFromPostURL(url):
    with YoutubeDL() as ydl:
        result = ydl.extract_info(url, download=False)
        return findApiFormat(result)

