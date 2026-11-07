from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import yt_dlp

app = FastAPI(title='声览音频服务')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])
ROOT = Path(__file__).parent

@app.get('/api/health')
def health():
    return {'ok': True, 'service': '声览'}

@app.get('/api/search')
def search(q: str = Query(min_length=2, max_length=160)):
    opts = {'quiet': True, 'no_warnings': True, 'skip_download': True, 'extract_flat': 'in_playlist', 'playlistend': 12, 'default_search': 'ytsearch12'}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(q, download=False)
        entries = info.get('entries', []) if info else []
        results = []
        for e in entries:
            if not e: continue
            results.append({'title': e.get('title') or '未命名音频', 'creator': e.get('uploader') or e.get('channel') or '未知来源', 'webpage_url': e.get('url') or e.get('webpage_url'), 'thumbnail': e.get('thumbnail'), 'duration': e.get('duration'), 'source': e.get('extractor_key') or '公开来源'})
        return {'results': results}
    except Exception as ex:
        return {'results': [], 'error': '暂时无法搜索该来源，请稍后重试。', 'detail': str(ex)[:300]}


@app.get('/api/audio')
def audio(url: str = Query(min_length=8, max_length=2000)):
    try:
        opts = {'quiet': True, 'no_warnings': True, 'format': 'bestaudio/best', 'skip_download': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info.get('entries'):
            info = next((x for x in info['entries'] if x), {})
        audio_url = info.get('url')
        if not audio_url:
            return {'error': '该内容没有可用的公开音频流。'}
        return {'url': audio_url}
    except Exception as ex:
        return {'error': '该来源暂时无法提取音频，请尝试其他内容。', 'detail': str(ex)[:250]}

@app.get('/', response_class=HTMLResponse)
def home():
    return (ROOT / 'index.html').read_text(encoding='utf-8')
