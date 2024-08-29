addEventListener('fetch', event => {
    event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
    const url = new URL(request.url)
    const path = url.pathname

    const match = path.match(/^\/vid\/([^\/]+)\/([^\/]+)\.mp4$/)
    if (!match) {
        return new Response('Invalid URL format', { status: 400 })
    }

    const author = match[1]
    const vid = match[2]

    const postLink = `https://www.tiktok.com/@${author}/video/${vid}`
    const videoData = await downloadVideoFromPostURL(postLink)
    if (!videoData) {
        return new Response('Failed to retrieve video', { status: 500 })
    }

    return new Response(videoData, {
        status: 200,
        headers: {
            'Content-Type': 'video/mp4'
        }
    })
}

async function getWebDataFromResponse(response) {
    if (response.status !== 200) {
        return null
    }
    const text = await response.text()
    const rx = /<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application\/json">(.*?)}<\/script>/
    const match = rx.exec(text)
    if (!match) {
        return null
    }
    const data = match[1] + "}"
    return JSON.parse(data)
}

function findApiFormat(videoInfo) {
    const vid = videoInfo.video
    const addr = (vid.downloadAddr == null || vid.downloadAddr != '') ? vid.downloadAddrAdr : vid.playAddr
    return {
        width: vid.width,
        height: vid.height,
        url: addr,
        thumb: vid.cover
    }
}

async function getVideoFromPostURL(url, includeCookies = false) {
    const response = await fetch(url, {
        headers: {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate'
        }
    })
    const videoInfo = await getWebDataFromResponse(response)
    if (!videoInfo || !videoInfo.__DEFAULT_SCOPE__['webapp.video-detail']) {
        return null
    }
    const vdata = videoInfo.__DEFAULT_SCOPE__['webapp.video-detail'].itemInfo.itemStruct
    if (includeCookies) {
        vdata.Cookies = response.headers.get('set-cookie')
        // only keep ttwid, tt_csrf_token, and tt_chain_token
        vdata.Cookies = vdata.Cookies.split(';').filter(c => c.includes('ttwid') || c.includes('tt_csrf_token') || c.includes('tt_chain_token')).join(';')
        vdata.Cookies = vdata.Cookies.replace(/;\s*httponly/gi, '')
        vdata.Cookies = vdata.Cookies.replace(/, /g, '; ')

    }
    return vdata
}

async function downloadVideoFromPostURL(url) {
    const videoInfo = await getVideoFromPostURL(url, true)
    if (!videoInfo) {
        return null
    }
    const vFormat = findApiFormat(videoInfo)
    const cookies = videoInfo.Cookies
    const headers = {
        'User-Agent': 'Mozilla/5.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate',
        'Accept-Encoding': 'gzip, deflate, br'
    }
    if (cookies) {
        headers['Cookie'] = cookies
    }

    const response = await fetch(vFormat.url, { headers })
    if (response.status !== 200) {
        return null
    }
    const videoBlob = await response.arrayBuffer()
    return new Uint8Array(videoBlob)
}
