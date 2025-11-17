# NOTICE 2025/11/17:

Due to a legal request, this service is no longer available.

# NOTICE 2025/07/11:
TikTok has blocked all methods I use for getting information from videos, and as I currently don't have the time to dedicate to this project, it is indefinitely on hold.

As a workaround to keep all vxtiktok.com links working properly, they will now redirect to an alternative service, kkTiktok, [which is hosted by kkscript](https://kkscript.com)

------
# vxtiktok
Basic Website that serves fixed TikTok video embeds to various platforms (i.e Discord) by using yt-dlp to grab TikTok video information. 
## How to use the hosted version

Just replace tiktok.com with vxtiktok.com on the link to the TikTok post! `https://www.tiktok.com/@username/video/1234567890123456789` -> `https://vxtiktok.com/@username/video/1234567890123456789`

## Other stuff

We handle various TikTok URL formats, including short mobile URLs and subdomain variants. The application will attempt to resolve these to the full TikTok URL before processing. Be sure to only replace "tiktok" in the url (i.e `vm.tiktok.com` -> `vm.vxtiktok.com`)

For TikTok posts containing multiple images, a slideshow video will be generated* (This can be done locally or via an external API, depending on the configuration.)

\* As of the time of writing, due to TikTok API changes this may not be working

**Note**: If you enjoy this service, please consider donating to help cover server costs. https://ko-fi.com/dylanpdx

## Limitations
- The application relies on TikTok's internal api; Changes made by them might break things
- Some features may not work for all types of TikTok content, especially non-video formats.
