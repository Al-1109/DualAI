from http.server import BaseHTTPRequestHandler
import json
from datetime import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_data = {
            'status': 'ok',
            'message': 'Webhook endpoint is active',
            'timestamp': str(datetime.now())
        }
        
        self.wfile.write(json.dumps(response_data).encode())
        return
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response_data = {
            'status': 'ok',
            'message': 'Webhook received',
            'received_bytes': content_length
        }
        
        self.wfile.write(json.dumps(response_data).encode())
        return 