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

if os.path.exists("vxTiktok.conf"):
    # as per python docs, "the most recently added configuration has the highest priority"
    # "conflicting keys are taken from the more recent configuration while the previously existing keys are retained"
    currentConfig.read("vxTiktok.conf")

with open("vxTiktok.conf", "w") as configfile:
    currentConfig.write(configfile) # write current config to file