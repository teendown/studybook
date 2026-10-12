"""Local preview with portable WebP/PWA MIME types (Windows registry independent)."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      '.webp': 'image/webp', '.webmanifest': 'application/manifest+json',
                      '.js': 'text/javascript', '.css': 'text/css'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(Path(__file__).parent / 'dist'), **kwargs)

    def log_message(self, *_):
        pass

if __name__ == '__main__':
    print('Preview: http://127.0.0.1:8765', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
