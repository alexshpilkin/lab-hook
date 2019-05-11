from http.server import BaseHTTPRequestHandler
from json import loads, dumps
from pprint import pprint

class HTTPRequestHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-Type', 'text/plain')
		self.end_headers()
		self.wfile.write(b'Hello world!\r\n')
		self.wfile.write('Path: {}\r\n'.format(self.path).encode('ascii'))

	def send_success(self):
		self.send_response(200)
		self.send_header('Content-Type', 'text/plain')
		self.end_headers()

	def do_POST(self):
		if self.path != '/':
			self.send_error(404)
		if self.headers.get('Content-Type') != 'application/json':
			self.send_error(400)
		try:
			length = int(self.headers.get('Content-Length'))
			event  = loads(self.rfile.read(length))
		except ValueError:
			self.send_error(400)
		pprint(event)

		if event['ref'] != 'refs/heads/master':
			return self.send_success()
		self.send_success()
		self.wfile.write('New head: {}\r\n'
		                 .format(event['after'])
		                 .encode('ascii'))


if __name__ == '__main__':
	from http.server import HTTPServer
	httpd = HTTPServer(('', 4567), HTTPRequestHandler)
	httpd.serve_forever()
