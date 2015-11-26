import datetime
from stem import Signal
from stem.control import Controller
from MyBrowser import MyBrowser
import random
from time import sleep
import socket

class UseTor(object):
    """
    Uses tor to change the IP so Zillow cant block the IP
    Also, uses mechanize to minic browser
    """

    
    def __init__(self,password, proxy_port,controller_port,pass_function=None):
        """
        password is for the set tor password
        proxy_port is the port use by the given tor
        pass_function is the function that given a html it will return True if not detected as ROBOT
        """
        self._password = password
        self._proxy_port = proxy_port
        self._controller_port = controller_port
        self._pass_function = pass_function
        self._br = MyBrowser(self._proxy_port)
        self._new_ip()        
        self._randtime()
        
    def _randtime(self):
        """
        Sets the date time used to change IP ever so often
        """
        ##change every 10 to 30 mins
        self._next_time = datetime.datetime.now() + datetime.timedelta(0,random.randint(600,1800))

        
    def _new_ip(self):
        """
        Changes the IP address that tor uses.
        It will check to make sure that the IP is not on Zillows Robot list or blocked list
        If on list will repeat new IP till not on list
        """
        def get_new_ip():
            with Controller.from_port(port = self._controller_port) as controller:
                controller.authenticate(self._password)
                controller.signal(Signal.NEWNYM)
                sleep(controller.get_newnym_wait())
                controller.close()
            
                
            # reset the browser and its settings by calling a new one
            self._br.close()
            self._br = MyBrowser(self._proxy_port)

            #reset the time before next change is required  
            self._randtime()
            
        get_new_ip()
        if self._pass_function != None:
            while(self._pass_function(self._br)==False):
                ##get_new till zillow doesn't fail robot test
                get_new_ip()
        
    
    def request(self,url):
        """
        Will return html of the requested url
        If needed it will change the Tor IP address to get the data
        """
        #see if it is time to find a new IP address 
        if datetime.datetime.now() > self._next_time:
            self._new_ip()

        ## try to connect to website and get the html
        try:
            r = self._br.open(url)
            html = r.read()
        except:
            self._new_ip()
            return self.request(url) #not successful try again
            
        # if pass function given and html received see if it passes the test function
        if self._pass_function != None:
            if self._pass_function(self._br, html=html)==False:
                self._new_ip()
                return self.request(url) #not successful try again

        # everything was successful return the html
        return html
