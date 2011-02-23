"""
Non-blender specific LRMDB interface handlers should go in here
"""

import xmlrpc.client, http.client

class DictCookies(dict):
	def parse_headers(self, headers):
		# Receive incoming cookies and store key:value pairs
		for header_name, header_value in headers:
			if header_name == 'Set-Cookie':
				#self._cookies.append(header_value)
				ck_pair = header_value.split(';')[0]
				ck_var, ck_val = ck_pair.split('=')
				self[ck_var] = ck_val
	def to_string(self):
		out = []
		for ck_pair in self.items():
			out.append( '%s=%s' % ck_pair )
		return ';'.join(out)

class CookieTransport(xmlrpc.client.Transport):
	# Custom user-agent string for this Transport
	user_agent = 'LuxBlend25'
	
	def __init__(self, *args, **kwargs):
		self._cookies = DictCookies()
		super().__init__(*args, **kwargs)
	
	# This method is almost identical to Transport.request
	def request(self, host, handler, request_body, verbose=False):
		# issue XML-RPC request
		http_conn = self.send_request(host, handler, request_body, verbose)
		resp = http_conn.getresponse()
		
		headers = resp.getheaders()
		
		# Extract cookies
		self._cookies.parse_headers(headers)
		
		if resp.status != 200:
			raise xmlrpc.client.ProtocolError(
				host + handler,
				resp.status, resp.reason,
				dict(headers)
				)
		
		self.verbose = verbose
		
		return self.parse_response(resp)
	
	# This method is identical to Transport.send_request
	def send_request(self, host, handler, request_body, debug):
		host, extra_headers, x509 = self.get_host_info(host)
		connection = http.client.HTTPConnection(host)
		if debug:
			connection.set_debuglevel(1)
		headers = {}
		if extra_headers:
			for key, val in extra_headers:
				headers[key] = val
		headers["Content-Type"] = "text/xml"
		headers["User-Agent"] = self.user_agent
		
		# Insert cookies
		headers["Cookie"] = self._cookies.to_string()
		
		connection.request("POST", handler, request_body, headers)
		return connection

class lrmdb_client(object):
	#static
	server = None
	
	@classmethod
	def server_instance(cls):
		if cls.server == None:
			cls.server = xmlrpc.client.ServerProxy(
				"http://www.luxrender.net/lrmdb2/ixr",
				transport=CookieTransport(),
				#verbose=True
			)
		
		return cls.server
