from flask import Flask, render_template, request, redirect
from yt_dlp import YoutubeDL
from flask_cors import CORS
import json
import cache
import config
import re
import requests

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
            return format
    # not found, search for the next best one
    for format in videoInfo['formats']:
        if format['url'].startswith('http://api'):
            return format
    # not found, return the first one
    return videoInfo['formats'][0]


def getVideoFromPostURL(url):
    with YoutubeDL() as ydl:
        result = ydl.extract_info(url, download=False)
        return result

def embed_tiktok(post_link):
    cachedItem = cache.getFromCache(post_link)
    if cachedItem != None:
        videoInfo = cache.getFromCache(post_link)
    else:
        videoInfo = getVideoFromPostURL(post_link)
        cache.addToCache(post_link, videoInfo)
    vFormat = findApiFormat(videoInfo)
    directURL = vFormat['url']
    return render_template('video.html', videoInfo=videoInfo,mp4URL=directURL,vFormat=vFormat,appname="vxTiktok")

@app.route('/')
def main():
    return redirect(config.currentConfig["MAIN"]["repoURL"])

@app.route('/<path:sub_path>')
def embedTiktok(sub_path):
    user_agent = request.headers.get('user-agent')
    baseURL = request.base_url
    # bug: if the link doesn't end up being https://www.tiktok.com (for example https://tiktok.com) yt-dlp can't parse it

    # if request.path is of the format /@username/video/1234567891234567891, add https://www.tiktok.com to the beginning
    if request.path.startswith("/@"):
        baseURL = "https://www.tiktok.com" + request.path
    else:
        domain = request.headers['Host']
        if "." not in domain:
            return "Error converting URL (Unsupported?)",500
        # subdomain can be "vm.vxtiktok.com", "id.vxtiktok.com", "en.vxtiktok.com", etc.
        # get main domain from subdomain
        subdomain = domain.split(".")[0]
        url = f"https://{subdomain}.tiktok.com{request.path}"
        # make a request and get the long URL for yt-dlp
        r = requests.get(url, allow_redirects=False)
        baseURL = r.headers['location']
        if baseURL == "https://www.tiktok.com/":
            return "Expired TikTok URL", 400
        print("Redirected to: " + baseURL)
    if user_agent in embed_user_agents:
        return embed_tiktok(baseURL)
    else:
        return redirect(baseURL)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
