#!/usr/bin/env python3
"""
AnimeSalt API - Vercel Minimal
============================
"""

import json
import re
import base64
import urllib.parse

# Try cloudscraper, fallback to urllib
try:
    import cloudscraper
    scraper = cloudscraper.create_scraper()
except:
    import urllib.request
    class SimpleScraper:
        def get(self, url, headers=None, timeout=30):
            req = urllib.request.Request(url)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            return urllib.request.urlopen(req, timeout=timeout)
        def post(self, url, data=None, headers=None, timeout=30):
            req = urllib.request.Request(url, data=data.encode() if data else None)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            return urllib.request.urlopen(req, timeout=timeout)
    scraper = SimpleScraper()

BASE_URL = "https://animesalt.ac"

def get_headers(ref="https://animesalt.ac/"):
    return {
        'User-Agent': 'Mozilla/5.0',
        'Referer': ref,
        'X-Requested-With': 'XMLHttpRequest'
    }

def get_home():
    try:
        resp = scraper.get(BASE_URL + '/', headers=get_headers())
        html = resp.text if hasattr(resp, 'text') else resp.read().decode()
        items = []
        for m in re.findall(r'href="(https://animesalt\.ac/(series|movies)/([^"]+))"', html):
            items.append({'url': m[0], 'type': m[1], 'slug': m[2]})
        return {'success': True, 'items': items[:20]}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_series(page=1):
    try:
        url = BASE_URL + '/series/'
        if page > 1:
            url += f'page/{page}/'
        resp = scraper.get(url, headers=get_headers())
        html = resp.text if hasattr(resp, 'text') else resp.read().decode()
        items = []
        for m in re.findall(r'href="(https://animesalt\.ac/series/([^"]+))"', html):
            if 'page' not in m[1]:
                items.append({'slug': m[1], 'url': m[0]})
        return {'success': True, 'items': items}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_movies(page=1):
    try:
        url = BASE_URL + '/movies/'
        if page > 1:
            url += f'page/{page}/'
        resp = scraper.get(url, headers=get_headers())
        html = resp.text if hasattr(resp, 'text') else resp.read().decode()
        items = []
        for m in re.findall(r'href="(https://animesalt\.ac/movies/([^"]+))"', html):
            if 'page' not in m[1]:
                items.append({'slug': m[1], 'url': m[0]})
        return {'success': True, 'items': items}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def get_anime_info(slug, itype=None):
    try:
        url = f'{BASE_URL}/{itype or "series"}/{slug}/'
        resp = scraper.get(url, headers=get_headers())
        html = resp.text if hasattr(resp, 'text') else resp.read().decode()
        title = re.search(r'<title>([^<]+)</title>', html)
        title = title.group(1) if title else slug
        
        episodes = []
        for m in re.findall(r'href="(https://animesalt\.ac/episode/[^"]+)"', html):
            ep_match = re.search(r'-(\d+)x(\d+)/', m)
            if ep_match:
                episodes.append({'url': m, 'season': int(ep_match.group(1)), 'episode': int(ep_match.group(2))})
        
        streams = []
        data_match = re.search(r'data=([A-Za-z0-9%_-]+)', html)
        if data_match:
            decoded = urllib.parse.unquote(data_match.group(1))
            decoded = base64.b64decode(decoded).decode()
            streams = json.loads(decoded)
        
        return {'success': True, 'slug': slug, 'title': title, 'episodes': episodes, 'streams': streams}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def search(q):
    try:
        resp = scraper.get(f'{BASE_URL}/?s={urllib.parse.quote(q)}', headers=get_headers())
        html = resp.text if hasattr(resp, 'text') else resp.read().decode()
        results = []
        for m in re.findall(r'href="(https://animesalt\.ac/(series|movies)/([^"]+))"', html):
            if 'page' not in m[1]:
                results.append({'slug': m[1], 'type': m[0], 'url': m[0]})
        return {'success': True, 'results': results}
    except Exception as e:
        return {'success': False, 'error': str(e)}


# Vercel app
def app(environ, start_response):
    """WSGI app for Vercel"""
    path = environ.get('PATH_INFO', '/')
    query = environ.get('QUERY_STRING', '')
    
    params = {}
    if query:
        for p in query.split('&'):
            if '=' in p:
                k, v = p.split('=', 1)
                params[k] = urllib.parse.unquote(v)
    
    try:
        if path == '/' or path == '':
            data = {'name': 'AnimeSalt API', 'version': '1.0.0', 'source': 'animesalt.ac'}
        elif path == '/home':
            data = get_home()
        elif path == '/series':
            data = get_series(int(params.get('page', 1)))
        elif path == '/movies':
            data = get_movies(int(params.get('page', 1)))
        elif path == '/info':
            data = get_anime_info(params.get('slug', ''), params.get('type'))
        elif path == '/search':
            data = search(params.get('q', ''))
        else:
            data = {'error': 'Not found'}
        
        body = json.dumps(data).encode()
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [body]
    except Exception as e:
        body = json.dumps({'error': str(e)}).encode()
        start_response('500 Error', [('Content-Type', 'application/json')])
        return [body]