import scrapezillow.scraper as scraper
from bs4 import BeautifulSoup
from pymongo import MongoClient
from time import sleep

def pass_function(br,url='http://www.zillow.com',html=None):
    """                                                                      
    Test to see if the program will get pass the url ROBOTS test
    """
    try:
        if html==None:
            r = br.open(url)
            html = r.read()
        soup = BeautifulSoup(html)
        return len(soup.findAll("div", { "class" : "captcha-container" }))!=1
    except:
        return False

class Scraper(object):
    def __init__(self,tor, zip_code):
        """
        Sets the data 
        """
        self._tor = tor
        # test tor
        self._zip_code = zip_code
        #Zillow database for housing description
        self._client = MongoClient('localhost', 27017)
        db = self._client.Zillow
        self._housing_description = db.housing_description
        
        #run the scraper
        self._get_zip_data()
        
    def _get_price_tax_url(self, soup):
        """
        Given the soup of the housing details html this will find and 
        return the ajaxURL for both price history and tax history 
        """
        groups = soup.text.split('ajaxURL')
        price_history, tax_history = None, None
        for group in groups[1:-1]:
            group = group.split(";")[0]
            if 'divId:"hdp-price-history"' in group:
                price_history = "http://www.zillow.com" + group.split('"')[1:2][0]
            elif 'divId:"hdp-tax-history"' in group:
                tax_history = "http://www.zillow.com" + group.split('"')[1:2][0]
        return price_history, tax_history

    def _populate_price_and_tax_histories(self,soup, results):
        """
        Change the code a little from scrapezillow.scraper
        Given a beatifulsoup it will use tor to request the data and
        populate the price and tax history
        """

        #get price and tax urls
        price_url, tax_url = self._get_price_tax_url(soup)

        ##populate price and tax history

        html = self._tor.request(price_url)
        soup = BeautifulSoup(html)
        results["price_history"] = self._get_price_history(soup)

        html = self._tor.request(tax_url)
        soup = BeautifulSoup(html)
        results["tax_history"] = self._get_tax_history(soup)

    def _get_price_history(self,soup):
        """
        Change the code a little from scrapezillow.scraper
        Given a beatifulsoup it will populate the price history
        """
        data =[]
        try:
            table_body = soup.find('table')
            rows = table_body.find_all('tr')
            for row in rows:
                try:
                    cols = row.find_all('td')
                    cols = [ele for ele in cols]
                    date = cols[0].get_text()
                    event = cols[1].get_text()
                    price_span = cols[2].find('span')
                    if not price_span:
                        price = None
                    else:
                        price = price_span.get_text()

                    data.append([date, event, price])
                except:
                    pass # undesired data
        except:
            pass #no table found
        return data

    def _get_tax_history(self,soup):
        """
        Change the code a little from scrapezillow.scraper
        Given a beatifulsoup it will populate the tax history
        """
        data = []
        try:
            table_body = soup.find('table')
            rows = table_body.find_all('tr')
            for row in rows:
                try:
                    cols = row.find_all('td')
                    cols = [ele for ele in cols]
                    date = cols[0].get_text()
                    tax = cols[1].contents[0]
                    assessment = cols[3].get_text()

                    data.append([date, tax, assessment])
                except:
                    pass # undesired data
        except:
            pass ##No table found
        return data

    def _scrape(self,html,url):
        """
        Scrape a specific zillow home. Takes either a url or a zpid. If both/neither are
        specified this function will throw an error.
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = scraper._get_property_summary(soup)
        results['url'] = url
        facts = scraper._parse_facts(scraper._get_fact_list(soup))
        results.update(**facts)
        results.update(**scraper._get_sale_info(soup))
        results["description"] = scraper._get_description(soup)
        results["photos"] = scraper._get_photos(soup)
        self._populate_price_and_tax_histories(soup, results)
        return results
        
        
    def _has_next(self,soup):
        """
        Looks for the Next button on the webpage to see if more houses 
        """
        if soup == None:
            return True
        return len(soup.findAll("li", { "class" : "zsg-pagination-next" }))==1
    
    def _get_house_links(self,soup):
        """
        Adds house details into the mongo database
        """
        for address in soup.findAll("dt", { "class" : "property-address" }):
            url = 'http://www.zillow.com'+address.find('a')['href']
            # Look up if already in the database
            if self._housing_description.find_one({'url':url})==None:
                try:
                    print url
                    html = self._tor.request(url)
                    self._housing_description.insert(self._scrape(html,url))
                    self._housing_description_gathered.append(url)
                    sleep(1)
                except:
                    ## scrape failed
                    ## missing data so just add url to not try to add again
                    self._housing_description.insert({'url':url})
    
    def _get_zip_data(self):
        """
        Finds the housing data for the zip
        """
        soup = None
        page = 1
        print 'Zip code:',self._zip_code,' started.'
        while(self._has_next(soup)):
            url = 'http://www.zillow.com/homes/recently_sold/'+str(self._zip_code)+'_rb/'+str(page)+'_p'
            r = self._tor.request(url)
            soup = BeautifulSoup(r)
            self._get_house_links(soup)
            page += 1
            sleep(1)
        print 'Zip code:',self._zip_code,' finished.'
        self._client.close()
