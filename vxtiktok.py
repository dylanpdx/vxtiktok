from urllib.parse import quote, urljoin, urlparse
import urllib.parse
from flask import Flask, render_template, request, redirect, send_file, abort
from flask_cors import CORS
import json
import cache
import config
import re
import requests
import io
import base64
import slideshowBuilder
import html
import urllib
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

tiktokArgs={}

def getWebDataFromResponse(response):
    if response.status_code != 200:
        return None
    # regex to find the json data: <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application\/json">(.*)}<\/script>
    rx = re.compile(r'<script *id="__UNIVERSAL_DATA_FOR_REHYDRATION__" *type="application\/json">(.*)}<\/script>')
    match = rx.search(response.text)
    if match == None:
        return None
    data = match.group(1) + "}"
    return json.loads(data)


def message(text):
    return render_template(
        'message.html', 
        message = text, 
        appname=config.currentConfig["MAIN"]["appName"])

def findApiFormat(videoInfo):
    vid = videoInfo['video']

    addr = None
    if "downloadAddr" in vid and vid["downloadAddr"] != None and vid["downloadAddr"] != "":
        addr = vid["downloadAddr"]
    else:
        addr = vid["playAddr"]

    return {"width": vid['width'], "height": vid['height'], "url": addr,"thumb":vid["cover"]}

def stripURL(url):
    return urljoin(url, urlparse(url).path)

def getVideoFromPostURL(url,includeCookies=False):
    rb = requests.get(url, headers={
        "User-Agent": "Mozilla/5.0",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Sec-Fetch-Mode": "navigate",
        "Accept-Encoding": "gzip, deflate, br"
    })
    videoInfo = getWebDataFromResponse(rb)

    if "webapp.video-detail" not in videoInfo["__DEFAULT_SCOPE__"]:
        return None

    vdata = videoInfo["__DEFAULT_SCOPE__"]["webapp.video-detail"]["itemInfo"]["itemStruct"]
    if includeCookies:
        vdata["Cookies"] = rb.cookies.get_dict()

    if isVFormatSlideshow(findApiFormat(vdata)):
        vdata["slideshowData"] = getSlideshowData(vdata)

    return vdata

def isVFormatSlideshow(vFormat):
    return vFormat['width'] == 0 and vFormat['height'] == 0

def downloadVideoFromPostURL(url):
    videoInfo = getVideoFromPostURL(url,includeCookies=True)
    vFormat = findApiFormat(videoInfo)

    if isVFormatSlideshow(vFormat):
        return None # this is a slideshow, not a video

    cookies = videoInfo["Cookies"]

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Sec-Fetch-Mode": "navigate",
        "Accept-Encoding": "gzip, deflate, br"
    }
    headers["Cookie"] = "; ".join([f"{k}={v}" for k,v in cookies.items()])


    r = requests.get(vFormat["url"], headers=headers)
    if r.status_code != 200:
        return None
    return r.content

def getSlideshowData(thisPost): # thsi function assumes the url is a slideshow
    postMusicURL = thisPost["music"]["playUrl"]
    postImages = thisPost["imagePost"]["images"]
    imageUrls=[]
    for image in postImages:
        for url in image["imageURL"]["urlList"]:
            if '.heic?' in url: # not supported by ffmpeg
                continue
            imageUrls.append(url)
            break

    finalData = {
        "musicURL": postMusicURL,
        "imageURLs": imageUrls
    }

    return finalData

def build_stats_line(videoInfo):
    videoInfo["view_count"] = videoInfo["stats"]["playCount"]
    videoInfo["like_count"] = videoInfo["stats"]["diggCount"]
    videoInfo["repost_count"] = videoInfo["stats"]["shareCount"]
    videoInfo["comment_count"] = videoInfo["stats"]["commentCount"]
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

def getVideoDataFromCacheOrDl(post_link):
    try:
        cachedItem = cache.getFromCache(post_link)
        if cachedItem != None:
            videoInfo = cachedItem
        else:
            videoInfo = getVideoFromPostURL(post_link)
            if videoInfo == None:
                return None
            cache.addToCache(post_link, videoInfo)
        return videoInfo
    except Exception as e:
        print(e)
        return None

def embed_tiktok(post_link):
    videoInfo = getVideoDataFromCacheOrDl(post_link)
    if videoInfo == None:
        return message("Failed to get video data from TikTok")
    if "slideshowData" not in videoInfo or videoInfo["slideshowData"] == None:
        vFormat = findApiFormat(videoInfo)

        directURL = f"https://"+config.currentConfig["MAIN"]["domainName"]+"/vid/"+videoInfo["author"]["uniqueId"]+"/"+videoInfo["id"]#+".mp4"
    else:
        vFormat = {"width": 1280, "height": 720, "cover":videoInfo["slideshowData"]["imageURLs"][0]}
        encoded_url=urllib.parse.quote(post_link)
        directURL = "https://"+config.currentConfig["MAIN"]["domainName"]+"/slideshow.mp4?url="+encoded_url
    statsLine = quote(build_stats_line(videoInfo))
    return render_template('video.html', videoInfo=videoInfo, mp4URL=directURL, vFormat=vFormat, appname=config.currentConfig["MAIN"]["appName"], statsLine=statsLine, domainName=config.currentConfig["MAIN"]["domainName"],original_url = post_link)

@app.route('/')
def main():
    return redirect(config.currentConfig["MAIN"]["repoURL"])

@app.route('/robots.txt')
def robots():
    return "User-agent: *\nDisallow: /"

@app.route('/vid/<author>/<vid>')
def video(author, vid):
    if vid.endswith(".mp4"):
        vid = vid[:-4]
    post_link = f"https://www.tiktok.com/@{author}/video/{vid}"
    videoData = downloadVideoFromPostURL(post_link)
    if videoData == None:
        abort(500)
    return send_file(io.BytesIO(videoData), mimetype='video/mp4')

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

@app.route('/slideshow.mp4')
def slideshow():
    url = request.args.get('url')
    url = stripURL(url)
    slideshow = getVideoDataFromCacheOrDl(url)
    if "slideshowData" not in slideshow:
        return "This is not a slideshow", 400
    if config.currentConfig["MAIN"]["slideshowRenderer"] != "local":
        renderer=config.currentConfig["MAIN"]["slideshowRenderer"] # this is a url to an api that should return raw mp4 data
        eurl=urllib.parse.quote(url)
        return redirect(f"{renderer}?url={eurl}",code=307)
    # render locally
    if config.currentConfig["MAIN"]["slideshowRenderer"] == "local":
        b64 = slideshowBuilder.generateVideo(slideshow)
        return send_file(io.BytesIO(base64.b64decode(b64)), mimetype='video/mp4')
        

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
        if subdomain != "vxtiktok":
            url = f"https://{subdomain}.tiktok.com{request.path}"
        else:
            url = f"https://tiktok.com{request.path}"
        # make a request and get the long URL for yt-dlp
        r = requests.get(url, allow_redirects=False)
        baseURL = r.headers['location']
        if baseURL == "https://www.tiktok.com/":
            return "Expired TikTok URL", 400
        print("Redirected to: " + baseURL)
    else:
        return "Error converting URL (Unsupported?)",500
    baseURL = stripURL(baseURL)
    if user_agent in embed_user_agents:
        baseURL = baseURL.replace("/photo/", "/video/")
        return embed_tiktok(baseURL)
    else:
        return redirect(baseURL)

if __name__ == "__main__":
    app.run(host='0.0.0.0')
