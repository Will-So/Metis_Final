import mechanize
import cookielib
from fake_useragent import UserAgent

class MyBrowser(object):
    """
    Uses Mechanize to act as browser
    The browser make use of the proxy port and host to get its data through
    """

    def __new__(self,proxy_port, proxy_host = 'localhost', debug=False):
        # Browser
        br = mechanize.Browser()

        # Cookie Jar
        cj = cookielib.LWPCookieJar()
        br.set_cookiejar(cj)

        # Browser options
        br.set_handle_equiv(True)
        br.set_handle_gzip(True)
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
            

        # User-Agent
        user_agent = UserAgent().random
        br.addheaders = [('User-agent', user_agent)]
        
        # Set the proxies to talk with tor
        br.set_proxies = {
            'http': 'socks5://'+proxy_host+':'+str(proxy_port), 
            'https': 'socks5://'+proxy_host+':'+str(proxy_port)
        }
        
        return br
