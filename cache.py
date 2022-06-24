from codecs import getdecoder
import config
import pymongo
from datetime import date,datetime, timedelta

client=None
db=None
if config.currentConfig["CACHE"]["cacheMethod"] == "mongodb":
    client = pymongo.MongoClient(config.currentConfig["CACHE"]["databaseurl"], connect=False)
    table = config.currentConfig["CACHE"]["databasetable"]
    db = client[table]

def getDefaultTTL():
    return datetime.today().replace(microsecond=0) + timedelta(days=1)

def addToCache(url,vidInfo):
    try:
        if config.currentConfig["CACHE"]["cacheMethod"] == "none":
            pass
        elif config.currentConfig["CACHE"]["cacheMethod"] == "mongodb":
            ttl=getDefaultTTL()
            db.linkCache.insert_one({"url":url,"info":vidInfo,"ttl":ttl})
    except Exception as e:
        print("addToCache for URL "+url+" failed: "+str(e))

def getFromCache(url):
    try:
        if config.currentConfig["CACHE"]["cacheMethod"] == "none":
            return None
        elif config.currentConfig["CACHE"]["cacheMethod"] == "mongodb":
            obj = db.linkCache.find_one({'url': url})
            if obj == None:
                return None
            return obj["info"]
    except Exception as e:
        print("getFromCache for URL "+url+" failed: "+str(e))
        return None