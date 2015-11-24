import mechanize
import cookielib
from fake_useragent import UserAgent
import urllib2
import httplib
import socks

class SocksiPyConnection(httplib.HTTPConnection):
    def __init__(self, proxytype, proxyaddr, proxyport = None, rdns = True, username = None, password = None, *args, **kwargs):
        self.proxyargs = (proxytype, proxyaddr, proxyport, rdns, username, password)
        httplib.HTTPConnection.__init__(self, *args, **kwargs)

    def connect(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(*self.proxyargs)
        if isinstance(self.timeout, float):
            self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

class SocksiPyHandler(urllib2.HTTPHandler):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kw = kwargs
        urllib2.HTTPHandler.__init__(self)

    def http_open(self, req):
        def build(host, port=None, strict=None, timeout=0):
            conn = SocksiPyConnection(*self.args, host=host, port=port, strict=strict, timeout=timeout, **self.kw)
            return conn
        return self.do_open(build, req)


class MyBrowser(object):
    """
    Uses Mechanize to act as browser
    The browser make use of the proxy port and host to get its data through
    """

    def __new__(self,proxy_port, proxy_host = 'localhost', debug=False):
        # Browser
        br = mechanize.Browser()

        # Use opener to connect to Tor
        opener = urllib2.build_opener(SocksiPyHandler(socks.PROXY_TYPE_SOCKS5, 'localhost', proxy_port))
        opener.addheaders = [('User-agent', UserAgent().random)]
        br.handlers = opener.handlers

        # Cookie Jar
        cj = cookielib.LWPCookieJar()
        br.set_cookiejar(cj)

        # Browser options
        br.set_handle_equiv(True)
        #br.set_handle_gzip(True)
        br.set_handle_redirect(True)
        br.set_handle_referer(True)
        br.set_handle_robots(False)

        # Follows refresh 0 but not hangs on refresh > 0
        br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

        # Want debugging messages?
        if debug:
            br.set_debug_http(True)
            br.set_debug_redirects(True)
            br.set_debug_responses(True)

        return br 
