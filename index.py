from http.server import BaseHTTPRequestHandler
from json import loads
from pprint import pprint
from urllib.request import Request, urlopen


def urlload(*args, **kwargs):
	with urlopen(*args, **kwargs) as fp:
		return loads(fp.read())


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

		if event['ref'] != 'refs/heads/master':
			return self.send_success()

		commit = urlload(event['repository']['commits_url']
		                      .replace('{/sha}', '/' + event['after']))
		tree = urlload(commit['commit']['tree']['url'] +
		               '?recursive=1')
		if tree.get('truncated', False):
			self.send_error(500)
		files = {file['path']: file for file in tree['tree']}

		file = files.get('iodide.json')
		if file is None:
			self.send_success()
			self.wfile.write('no iodide.json found'
			                 .encode('ascii'))
			return
		if file['type'] != 'blob':
			return self.send_error('400')
		req = Request(file['url'],
		              headers={'Accept': 'application/vnd.github.raw'})
		with urlopen(req) as fp:
			try:
				config = loads(fp.read())
				if not isinstance(config, dict):
					raise ValueError('not a dictionary')
				notebooks = config.get('notebooks', {})
				if not isinstance(notebooks, dict):
					raise ValueError('not a dictionary')
				if not all(isinstance(v, str)
				           for v in notebooks.values()):
					raise ValueError('not a string')
			except ValueError as e:
				return self.send_error(400)

		for name, url in notebooks.items():
			file = files.get(name)
			if file is None:
				return self.send_error(400)
			req = Request(file['url'],
			              headers={'Accept': 'application/vnd.github.raw'})
			with urlopen(req) as fp:
				data = fp.read()
			print(name, url, data)

		self.send_success()
		self.wfile.write('New head: {}\r\n'
		                 .format(event['after'])
		                 .encode('ascii'))


if __name__ == '__main__':
	from http.server import HTTPServer
	httpd = HTTPServer(('', 4567), HTTPRequestHandler)
	httpd.serve_forever()
