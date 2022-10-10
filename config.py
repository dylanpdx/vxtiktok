import configparser
import os

currentConfig = configparser.ConfigParser()

## default values

currentConfig["MAIN"]={
    "appName": "vxTiktok",
    "embedColor": "#EE1D52",
    "repoURL":"https://github.com/dylanpdx/vxtiktok",
    "domainName":"vxtiktok.com",
}

currentConfig["CACHE"]={
    "cacheMethod":"none",
    "databaseURL":"{mongodb URL}",
    "databaseTable":"vxTiktok",
    "cacheTTL":86400,
}

if 'RUNNING_SERVERLESS' in os.environ and os.environ['RUNNING_SERVERLESS'] == '1':
    currentConfig["MAIN"]={
        "appName": os.environ['APP_NAME'],
        "embedColor": "#EE1D52",
        "repoURL":os.environ['REPO_URL'],
        "domainName":os.environ['DOMAINNAME'],
    }
    currentConfig["CACHE"]={
        "cacheMethod":os.environ['CACHE_METHOD'],
        "databaseURL":os.environ['DATABASE_URL'],
        "databaseTable":os.environ['CACHE_TABLE'],
        "cacheTTL":int(os.environ['CACHE_TTL']),
    }
else:
    if os.path.exists("vxTiktok.conf"):
        # as per python docs, "the most recently added configuration has the highest priority"
        # "conflicting keys are taken from the more recent configuration while the previously existing keys are retained"
        currentConfig.read("vxTiktok.conf")

    with open("vxTiktok.conf", "w") as configfile:
        currentConfig.write(configfile) # write current config to file