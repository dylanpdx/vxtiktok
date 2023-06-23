import base64
import os
import subprocess
import json
import sys
import tempfile

def generateVideo(slideshowVideoData):
    # slideshowData = {..., "slideshowData":{"musicUrl":"","imageUrls":[]}}
    slideshowData = slideshowVideoData["slideshowData"]
    txtData = ""
    for url in slideshowData["imageURLs"]:
        txtData += f"file '{url}'\nduration 2\n"
    with tempfile.TemporaryDirectory() as tmpdirname:
        txtPath = os.path.join(tmpdirname, "test.txt")
        with open(txtPath, "w") as f:
            f.write(txtData)
        musicPath = slideshowData["musicURL"]
        outputFilePath = os.path.join(tmpdirname, "out.mp4")
        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-protocol_whitelist", "file,http,tcp,https,tls", "-i", txtPath, "-i", musicPath, "-map", "0:v", "-map", "1:a","-vf","pad=ceil(iw/2)*2:ceil(ih/2)*2", "-shortest", outputFilePath])
        with open(outputFilePath, "rb") as vid_file:
            encoded_string = base64.b64encode(vid_file.read()).decode('ascii')
    return encoded_string