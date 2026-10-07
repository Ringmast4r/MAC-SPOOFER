import hmac
import json
import mimetypes
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit, parse_qs
from . import BUNDLE

PORT = 8802

def start_server(service, desktop=None, port=PORT):
    token = secrets.token_urlsafe(32)
    public = BUNDLE / 'public'
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args): pass

        def send(self, code, body, content_type='application/json; charset=utf-8'):
            if not isinstance(body, bytes): body = json.dumps(body).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control','no-store')
            self.send_header('X-Content-Type-Options','nosniff')
            self.send_header('X-Frame-Options','DENY')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
            self.end_headers()
            try: self.wfile.write(body)
            except (ConnectionResetError, BrokenPipeError): pass

        def trusted(self, api=False):
            host = '127.0.0.1:' + str(self.server.server_port)
            if self.headers.get('Host') != host: return False
            origin = self.headers.get('Origin')
            if origin and origin != 'http://' + host: return False
            if self.headers.get('Sec-Fetch-Site') == 'cross-site': return False
            return not api or hmac.compare_digest(self.headers.get('X-MAC-Token',''),token)

        def do_GET(self):
            url = urlsplit(self.path)
            if not self.trusted(url.path.startswith('/api/')):
                self.send(403, {'error':'This request is not from the app session.'}); return
            try:
                args = parse_qs(url.query)
                if url.path == '/api/state': self.send(200,service.state()); return
                if url.path == '/api/search': self.send(200,service.catalog.search(args.get('q',[''])[0])); return
                if url.path == '/api/inspect': self.send(200,service.catalog.inspect(args.get('mac',[''])[0])); return
                if url.path == '/api/export': self.send(200,service.state()); return
                names = {'/':'index.html','/css/style.css':'css/style.css','/js/app.js':'js/app.js','/img/nw-globe.png':'img/nw-globe.png'}
                if url.path not in names: self.send(404,{'error':'Not found'}); return
                path = public / names[url.path]
                body = path.read_bytes()
                if path.suffix == '.html': body = body.replace(b'__SESSION_TOKEN__',token.encode())
                self.send(200,body,(mimetypes.guess_type(str(path))[0] or 'application/octet-stream')+'; charset=utf-8')
            except ValueError as exc: self.send(400,{'error':str(exc)})
            except Exception as exc: self.send(500,{'error':str(exc)})

        def do_POST(self):
            if not self.trusted(True): self.send(403,{'error':'This request is not from the app session.'}); return
            try:
                length = int(self.headers.get('Content-Length','0'))
                if length < 0 or length > 8192: raise ValueError('Request too large.')
                if self.headers.get('Content-Type','').split(';')[0] != 'application/json': raise ValueError('JSON is required.')
                body = json.loads(self.rfile.read(length) or b'{}')
                if not isinstance(body,dict): raise ValueError('Expected an object.')
                if self.path == '/api/refresh': result = service.refresh()
                elif self.path == '/api/generate': result = service.catalog.generate(body.get('prefix'))
                elif self.path == '/api/theme': result = service.theme(body.get('theme'))
                elif self.path == '/api/ready':
                    service.ui = {key:body.get(key) for key in ('title','ready','adapters','theme')}
                    result = {'ok':True}
                elif self.path == '/api/change': result = service.change(body.get('id'), body.get('address'), body.get('confirmed') is True)
                elif self.path in ('/api/quit','/api/elevate','/api/repo'):
                    if not desktop: raise ValueError('This action is available in the desktop window.')
                    result = getattr(desktop, self.path.split('/')[-1])()
                else: self.send(404,{'error':'Not found'}); return
                self.send(200,result or {'ok':True})
            except PermissionError as exc: self.send(403,{'error':str(exc)})
            except (ValueError, TypeError) as exc: self.send(400,{'error':str(exc)})
            except Exception as exc: self.send(500,{'error':str(exc)})
    server = ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever,daemon=True).start()
    return server, 'http://127.0.0.1:' + str(server.server_port) + '/'
