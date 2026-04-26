#!/usr/bin/env python3
"""
AnimeSalt API - Vercel Deployment Ready
==================================
Full API for animesalt.ac streaming site
"""

import sys
import os
import json
import re
import base64
import urllib.parse

# Handle import for local vs Vercel
try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    import subprocess
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'cloudscraper', '-q'], timeout=60)
        import cloudscraper
        HAS_CLOUDSCRAPER = True
    except:
        cloudscraper = None

# If cloudscraper not available, create a simple fallback
if not HAS_CLOUDSCRAPER:
    import urllib.request
    
    class SimpleScraper:
        """Simple fallback if cloudscraper not available"""
        def __init__(self):
            self.opener = urllib.request.build_opener()
            self.opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]
        
        def get(self, url, headers=None, timeout=30, allow_redirects=True):
            req = urllib.request.Request(url)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            return self.opener.open(req, timeout=timeout)
        
        def post(self, url, data=None, headers=None, timeout=30):
            req = urllib.request.Request(url, data=data.encode() if data else None)
            if headers:
                for k, v in headers.items():
                    req.add_header(k, v)
            return self.opener.open(req, timeout=timeout)
    
    class cloudscraper:
        @staticmethod
        def create_scraper():
            return SimpleScraper()


DEFAULT_REFERER = "https://animesalt.ac/"
PLAYER_URL = "https://as-cdn21.top/player/index.php"


class AnimeSaltAPI:
    """AnimeSalt API client"""
    
    BASE_URL = "https://animesalt.ac"
    
    def __init__(self):
        self.scraper = cloudscraper.create_scraper()
        
    def _get_headers(self, referer: str = None) -> dict:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/javascript, */*',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': referer or DEFAULT_REFERER,
            'Referer': referer or DEFAULT_REFERER,
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    def get_home(self) -> dict:
        """Get homepage content"""
        try:
            resp = self.scraper.get(self.BASE_URL + '/', headers=self._get_headers(), timeout=30)
            html = resp.text
            
            items = []
            links = re.findall(r'href=\"(https://animesalt\.ac/(series|movies)/([^\"]+))\"', html)
            seen = set()
            for full_url, content_type, slug in links:
                if slug and slug not in seen and not slug.startswith('page'):
                    seen.add(slug)
                    items.append({
                        'slug': slug,
                        'type': content_type,
                        'url': full_url
                    })
            
            return {'success': True, 'items': items[:30], 'total': len(items)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_series(self, page: int = 1) -> dict:
        """Get series list"""
        try:
            url = f"{self.BASE_URL}/series/"
            if page > 1:
                url += f"page/{page}/"
            
            resp = self.scraper.get(url, headers=self._get_headers(), timeout=30)
            html = resp.text
            
            items = []
            links = re.findall(r'href=\"(https://animesalt\.ac/series/([^\"]+))\"', html)
            for link, slug in links:
                if '/series/page/' not in slug and slug and not slug.startswith('page'):
                    items.append({'slug': slug.rstrip('/'), 'url': link})
            
            return {'success': True, 'items': items, 'page': page, 'has_more': len(items) >= 20}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_movies(self, page: int = 1) -> dict:
        """Get movies list"""
        try:
            url = f"{self.BASE_URL}/movies/"
            if page > 1:
                url += f"page/{page}/"
            
            resp = self.scraper.get(url, headers=self._get_headers(), timeout=30)
            html = resp.text
            
            items = []
            links = re.findall(r'href=\"(https://animesalt\.ac/movies/([^\"]+))\"', html)
            for link, slug in links:
                if '/movies/page/' not in slug and slug and not slug.startswith('page'):
                    items.append({'slug': slug.rstrip('/'), 'url': link})
            
            return {'success': True, 'items': items, 'page': page, 'has_more': len(items) >= 20}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_category(self, category: str, page: int = 1) -> dict:
        """Get anime by category"""
        try:
            url = f"{self.BASE_URL}/category/{category}/"
            if page > 1:
                url += f"page/{page}/"
            
            resp = self.scraper.get(url, headers=self._get_headers(), timeout=30)
            html = resp.text
            
            items = []
            links = re.findall(r'href=\"(https://animesalt\.ac/(series|movies)/([^\"]+))\"', html)
            for full_url, content_type, slug in links:
                if slug and not slug.startswith('page'):
                    items.append({'slug': slug, 'type': content_type, 'url': full_url})
            
            return {'success': True, 'items': items, 'category': category, 'page': page}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_anime_info(self, slug: str, anime_type: str = None) -> dict:
        """Get anime details"""
        try:
            if anime_type:
                url = f"{self.BASE_URL}/{anime_type}/{slug}/"
            else:
                url = f"{self.BASE_URL}/series/{slug}/"
                resp = self.scraper.get(url, headers=self._get_headers(), timeout=30)
                if resp.status_code != 200:
                    url = f"{self.BASE_URL}/movies/{slug}/"
            
            resp = self.scraper.get(url, headers=self._get_headers(), timeout=30)
            html = resp.text
            
            title = re.search(r'<title>([^\(<]+)</title>', html)
            title = title.group(1).strip() if title else slug
            
            anime_type = 'series' if '/series/' in url else 'movies'
            
            poster = ''
            posters = re.findall(r'(?:data-src|src)=\"(https://img\.animesalt\.ac/images-unified/[^\"]+)', html)
            if posters:
                poster = posters[0]
            
            genres = []
            cats = re.findall(r'/category/([^\"/]+)/', html)
            genres = list(set(cats))
            
            year = ''
            year_match = re.search(r'(\d{4})', html)
            if year_match:
                year = year_match.group(1)
            
            episodes = []
            streams = []
            
            if anime_type == 'series':
                eps = re.findall(r'href=\"(https://animesalt\.ac/episode/[^\"]+)\"', html)
                for ep in list(set(eps)):
                    m = re.search(r'-(\d+)x(\d+)/', ep)
                    if m:
                        episodes.append({'url': ep, 'season': int(m.group(1)), 'episode': int(m.group(2))})
            else:
                player_data = re.search(r'data=([A-Za-z0-9%_-]+)', html)
                if player_data:
                    encoded = player_data.group(1)
                    decoded = urllib.parse.unquote(encoded)
                    decoded = base64.b64decode(decoded).decode()
                    links = json.loads(decoded)
                    for link in links:
                        streams.append({'language': link.get('language', ''), 'link': link.get('link', '')})
            
            return {
                'success': True,
                'slug': slug,
                'type': anime_type,
                'title': title,
                'poster': poster,
                'genres': genres,
                'year': year,
                'episodes': episodes,
                'streams': streams,
                'url': url
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_episodes(self, slug: str) -> dict:
        """Get episode list for series"""
        info = self.get_anime_info(slug, 'series')
        if info['success']:
            return {'success': True, 'slug': slug, 'episodes': info.get('episodes', [])}
        return info
    
    def search(self, query: str) -> dict:
        """Search anime"""
        try:
            url = f"{self.BASE_URL}/?s={urllib.parse.quote(query)}"
            resp = self.scraper.get(url, headers=self._get_headers(), timeout=30)
            html = resp.text
            
            results = []
            items = re.findall(r'href=\"(https://animesalt\.ac/(series|movies)/([^\"]+))\"', html)
            for full_url, content_type, slug in items:
                if slug and not slug.startswith('page'):
                    results.append({'title': slug.replace('-', ' ').title(), 'url': full_url, 'type': content_type})
            
            return {'success': True, 'results': results, 'query': query}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_stream_data(self, video_id: str, referer: str = None) -> dict:
        """Get stream data from player"""
        headers = self._get_headers(referer)
        url = f"{PLAYER_URL}?data={video_id}&do=getVideo"
        resp = self.scraper.post(url, data={'hash': video_id, 'r': referer or DEFAULT_REFERER}, headers=headers)
        
        try:
            data = json.loads(resp.text)
            m3u8 = data.get('videoSource', '').replace('\\/', '/')
            
            return {
                'success': True,
                'video_id': video_id,
                'm3u8': m3u8,
                'secured_link': data.get('securedLink', '').replace('\\/', '/'),
                'poster': data.get('videoImage', ''),
                'hls': data.get('hls', False),
                'ck': data.get('ck', '')
            }
        except:
            return {'success': False, 'error': resp.text[:200]}
    
    def get_episode_stream(self, episode_url: str) -> dict:
        """Get stream from episode URL"""
        try:
            resp = self.scraper.get(episode_url, headers=self._get_headers(), timeout=30)
            html = resp.text
            
            # Movies: base64 encoded data
            match = re.search(r'data=([A-Za-z0-9%_-]+)', html)
            if match:
                encoded = match.group(1)
                encoded = urllib.parse.unquote(encoded)
                decoded = base64.b64decode(encoded).decode()
                links = json.loads(decoded)
                results = [{'language': link.get('language', ''), 'link': link.get('link', '')} for link in links]
                return {'success': True, 'streams': results, 'episode_url': episode_url}
            
            # Series: iframe with video ID
            iframe_match = re.search(r'<iframe[^>]+src=\"(https://[^\"]+)\"', html)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                video_id = iframe_url.split('/')[-1]
                stream_data = self.get_stream_data(video_id)
                stream_data['episode_url'] = episode_url
                return stream_data
            
            return {'success': False, 'error': 'No stream data found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def resolve_short_url(self, short_url: str) -> str:
        """Resolve short.icu URL"""
        try:
            resp = self.scraper.get(short_url, headers=self._get_headers(), timeout=30, allow_redirects=False)
            if resp.status_code == 302:
                return resp.headers.get('Location', '')
            return short_url
        except:
            return short_url
    
    def get_stream_from_short_url(self, short_url: str) -> dict:
        """Get stream data from short URL"""
        try:
            resolved = self.resolve_short_url(short_url)
            if resolved == short_url:
                return {'success': False, 'error': 'Could not resolve'}
            
            return {'success': True, 'short_url': short_url, 'resolved_url': resolved}
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Create API instance
api = AnimeSaltAPI()


# Vercel handler
def handler(request, context):
    """Vercel API handler"""
    # Handle both Vercel and direct calls
    try:
        path = getattr(request, 'path', request.url.path if hasattr(request, 'url') else '/')
        query = getattr(request, 'query', request.url.query if hasattr(request, 'url') else '')
    except:
        path = '/'
        query = ''
    
    # Parse query params
    params = {}
    if query:
        for param in query.split('&'):
            if '=' in param:
                k, v = param.split('=', 1)
                params[k] = v
    
    try:
        if path == '/' or path == '':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({
                    'name': 'AnimeSalt API',
                    'version': '1.0.0',
                    'source': 'animesalt.ac',
                    'endpoints': ['/', '/home', '/series', '/movies', '/category', '/info', '/episodes', '/search', '/stream', '/resolve']
                })
            }
        
        elif path == '/test-animesalt':
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'name': 'AnimeSalt API TEST', 'source': 'animesalt.ac'})}
        
        elif path == '/home':
            result = api.get_home()
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(result)}
        
        elif path == '/series':
            page = int(params.get('page', 1))
            result = api.get_series(page)
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(result)}
        
        elif path == '/movies':
            page = int(params.get('page', 1))
            result = api.get_movies(page)
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(result)}
        
        elif path == '/category':
            category = params.get('category', 'anime')
            page = int(params.get('page', 1))
            result = api.get_category(category, page)
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(result)}
        
        elif path == '/info':
            slug = params.get('slug', '')
            anime_type = params.get('type', None)
            if not slug:
                return {'statusCode': 400, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': 'slug required'})}
            result = api.get_anime_info(slug, anime_type)
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(result)}
        
        elif path == '/episodes':
            slug = params.get('slug', '')
            if not slug:
                return {'statusCode': 400, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': 'slug required'})}
            result = api.get_episodes(slug)
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(result)}
        
        elif path == '/search':
            query = params.get('q', params.get('query', ''))
            if not query:
                return {'statusCode': 400, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': 'query required'})}
            result = api.search(query)
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(result)}
        
        elif path == '/stream':
            url = params.get('url', '')
            video_id = params.get('video_id', '')
            
            if url:
                result = api.get_episode_stream(url)
            elif video_id:
                result = api.get_stream_data(video_id)
            else:
                return {'statusCode': 400, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': 'url or video_id required'})}
            
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps(result)}
        
        elif path == '/resolve':
            url = params.get('url', '')
            if not url:
                return {'statusCode': 400, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': 'url required'})}
            result = api.resolve_short_url(url)
            return {'statusCode': 200, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'success': True, 'resolved': result})}
        
        else:
            return {'statusCode': 404, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': 'Not found'})}
    
    except Exception as e:
        return {'statusCode': 500, 'headers': {'Content-Type': 'application/json'}, 'body': json.dumps({'error': str(e)})}


# Vercel needs 'app' as top-level for Python runtime
app = handler