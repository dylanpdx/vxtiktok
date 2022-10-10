from codecs import getdecoder
import config
import pymongo
import boto3
from datetime import date,datetime, timedelta

client=None
db=None
DYNAMO_CACHE_TBL=None
if config.currentConfig["CACHE"]["cacheMethod"] == "mongodb":
    client = pymongo.MongoClient(config.currentConfig["CACHE"]["databaseurl"], connect=False)
    table = config.currentConfig["CACHE"]["databasetable"]
    db = client[table]
elif config.currentConfig["CACHE"]["cacheMethod"]=="dynamodb":
    DYNAMO_CACHE_TBL=config.currentConfig["CACHE"]["databasetable"]
    client = boto3.resource('dynamodb')

def getDefaultTTL():
    return datetime.today().replace(microsecond=0) + timedelta(days=1)

def addToCache(url,vidInfo):
    try:
        if config.currentConfig["CACHE"]["cacheMethod"] == "none":
            pass
        elif config.currentConfig["CACHE"]["cacheMethod"] == "mongodb":
            ttl=getDefaultTTL()
            db.linkCache.insert_one({"url":url,"info":vidInfo,"ttl":ttl})
        elif config.currentConfig["CACHE"]["cacheMethod"] == "dynamodb":
            ttl=getDefaultTTL()
            ttl = int(ttl.strftime('%s'))
            table = client.Table(DYNAMO_CACHE_TBL)
            table.put_item(Item={"url":url,"info":vidInfo,"ttl":ttl})
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
        elif config.currentConfig["CACHE"]["cacheMethod"] == "dynamodb":
            obj = client.Table(DYNAMO_CACHE_TBL).get_item(Key={'url': url})
            if 'Item' not in obj:
                return None
            return obj["Item"]["info"]
    except Exception as e:
        print("getFromCache for URL "+url+" failed: "+str(e))
        return None