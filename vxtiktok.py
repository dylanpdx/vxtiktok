from flask import Flask, render_template, request
from yt_dlp import YoutubeDL
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

embed_user_agents = [
    "facebookexternalhit/1.1",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36",
    "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US; Valve Steam Client/default/1596241936; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36",
    "Mozilla/5.0 (Windows; U; Windows NT 10.0; en-US; Valve Steam Client/default/0; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36", 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/601.2.4 (KHTML, like Gecko) Version/9.0.1 Safari/601.2.4 facebookexternalhit/1.1 Facebot Twitterbot/1.0", 
    "facebookexternalhit/1.1",
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; Valve Steam FriendsUI Tenfoot/0; ) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36", 
    "Slackbot-LinkExpanding 1.0 (+https://api.slack.com/robots)", 
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:38.0) Gecko/20100101 Firefox/38.0", 
    "Mozilla/5.0 (compatible; Discordbot/2.0; +https://discordapp.com)", 
    "TelegramBot (like TwitterBot)", 
    "Mozilla/5.0 (compatible; January/1.0; +https://gitlab.insrt.uk/revolt/january)", 
    "test"]

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


def getVideoFromPostURL(url):
    with YoutubeDL() as ydl:
        result = ydl.extract_info(url, download=False)
        return result

def embed_tiktok(post_link):
    videoInfo = getVideoFromPostURL(post_link)
    directURL = findApiFormat(videoInfo)
    return render_template('video.html', videoInfo=videoInfo,mp4URL=directURL,appname="vxTiktok")

@app.route('/')
def main():
    return ""

@app.route('/<path:sub_path>')
def embedTiktok(sub_path):
    baseURL = request.base_url
    baseURL=baseURL.replace("vxtiktok","tiktok")
    return embed_tiktok(baseURL)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
