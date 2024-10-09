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

    if len(slideshowData["imageURLs"]) == 1:
        slideshowData["imageURLs"].append(slideshowData["imageURLs"][0])

    for url in slideshowData["imageURLs"]:
        txtData += f"file '{url}'\nduration 2\n"
    with tempfile.TemporaryDirectory() as tmpdirname:
        txtPath = os.path.join(tmpdirname, "test.txt")
        with open(txtPath, "w") as f:
            f.write(txtData)
        musicPath = slideshowData["musicURL"]
        outputFilePath = os.path.join(tmpdirname, "out.mp4")
        subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-protocol_whitelist", "file,http,tcp,https,tls", "-i", txtPath, "-i", musicPath, "-map", "0:v", "-map", "1:a","-vf","scale=1280:720:force_original_aspect_ratio=decrease:eval=frame,pad=1280:720:-1:-1:eval=frame,format=yuv420p", "-filter_complex", "[1:0] apad","-shortest", outputFilePath])
        with open(outputFilePath, "rb") as vid_file:
            encoded_string = base64.b64encode(vid_file.read()).decode('ascii')
    return encoded_string