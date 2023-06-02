from urllib.parse import quote
from flask import Flask, render_template, request, redirect
from yt_dlp import YoutubeDL
from flask_cors import CORS
import json
import cache
import config
import re
import requests
import io
import base64

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

        if result["formats"][0]["width"] == 0 and result["formats"][0]["height"] == 0:
            # this is most likely a slideshow
            return getSlideshowDataFromPostURL(url)
        result["slideshowData"] = None
        return result

def getSlideshowDataFromPostURL(url): # thsi function assumes the url is a slideshow
    with YoutubeDL(params={"dump_intermediate_pages":True}) as ydl:
        f = io.StringIO()
        ydl._out_files.screen = f # this is a hack to get the output of ydl to a variable
        result = ydl.extract_info(url, download=False)
        s=f.getvalue()
        # find the first line that's valid base64 data
        data=None
        for line in s.splitlines():
            if re.match(r"^[A-Za-z0-9+/=]+$", line):
                data= json.loads(base64.b64decode(line).decode())
        thisPost = data["aweme_list"][0]
        postMusicURL = thisPost["music"]["play_url"]["uri"]
        postImages = thisPost["image_post_info"]["images"]
        imageUrls=[]
        for image in postImages:
            imageUrls.append(image["display_image"]["url_list"][0])

        finalData = {
            "musicURL": postMusicURL,
            "imageURLs": imageUrls
        }
        result["slideshowData"] = finalData

        return result

def build_stats_line(videoInfo):
    if videoInfo['view_count'] > 0 or videoInfo['like_count'] > 0 or videoInfo['repostCount'] > 0 or videoInfo['comment_count'] > 0:
        text = ""

        if videoInfo['view_count'] > 0:
            text += f"{videoInfo['view_count']} 👁️    "
        if videoInfo['like_count'] > 0:
            text += f"{videoInfo['like_count']} ❤️    "
        if videoInfo['repost_count'] > 0:
            text += f"{videoInfo['repost_count']} 🔁    "
        if videoInfo['comment_count'] > 0:
            text += f"{videoInfo['comment_count']} 💬    "
        return text
    else:
        return ""

def embed_tiktok(post_link):
    cachedItem = cache.getFromCache(post_link)
    if cachedItem != None:
        videoInfo = cachedItem
    else:
        videoInfo = getVideoFromPostURL(post_link)
        cache.addToCache(post_link, videoInfo)
    vFormat = findApiFormat(videoInfo)
    directURL = vFormat['url']
    statsLine = quote(build_stats_line(videoInfo))
    return render_template('video.html', videoInfo=videoInfo, mp4URL=directURL, vFormat=vFormat, appname=config.currentConfig["MAIN"]["appName"], statsLine=statsLine, domainName=config.currentConfig["MAIN"]["domainName"])

@app.route('/')
def main():
    return redirect(config.currentConfig["MAIN"]["repoURL"])

@app.route('/owoembed')
def alternateJSON():
    return {
        "author_name": request.args.get('text'),
        "author_url": request.args.get('url'),
        "provider_name": config.currentConfig["MAIN"]["appName"],
        "provider_url": config.currentConfig["MAIN"]["repoURL"],
        "title": "TikTok",
        "type": "link",
        "version": "1.0"
    }

@app.route('/<path:sub_path>')
def embedTiktok(sub_path):
    user_agent = request.headers.get('user-agent')
    baseURL = request.base_url
    # bug: if the link doesn't end up being https://www.tiktok.com (for example https://tiktok.com) yt-dlp can't parse it

    # if request.path is of the format /@username/video/1234567891234567891, add https://www.tiktok.com to the beginning
    if request.path.startswith("/@"):
        baseURL = "https://www.tiktok.com" + request.path
    elif request.path.startswith("/t/"):
        # short mobile url, need to resolve to longer one
        r = requests.get(f"https://www.tiktok.com{request.path}", allow_redirects=False)
        baseURL = r.headers['location']
    elif "." in request.headers['Host']:
        # subdomain can be "vm.vxtiktok.com", "id.vxtiktok.com", "en.vxtiktok.com", etc.
        # get main domain from subdomain
        subdomain = (request.headers['Host']).split(".")[0]
        url = f"https://{subdomain}.tiktok.com{request.path}"
        # make a request and get the long URL for yt-dlp
        r = requests.get(url, allow_redirects=False)
        baseURL = r.headers['location']
        if baseURL == "https://www.tiktok.com/":
            return "Expired TikTok URL", 400
        print("Redirected to: " + baseURL)
    else:
        return "Error converting URL (Unsupported?)",500

    if user_agent in embed_user_agents:
        return embed_tiktok(baseURL)
    else:
        return redirect(baseURL)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
