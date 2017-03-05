import scrapy
import datetime
import re
import sys
import urllib
#import js2xml
#import json
import requests
import logging
import os

class extraBeerSpider(scrapy.Spider):
    name = "extraBeerSpider"
    #download_delay = 1.5
    #custom_settings = {
        #ROBOTSTXT_OBEY=True
    #}
    logging.getLogger('scrapy').setLevel(logging.INFO)

    def __init__(self, category=None, *args, **kwargs):
        super(extraBeerSpider, self).__init__(*args, **kwargs)
        target_url = 'http://buscando.extra.com.br/?'

        #attrs
        strProducts = str(getattr(self, 'product', 'cerveja'))
        beerMode = str(getattr(self, 'beerMode',False))
        #size = 'size=' + getattr(self,'rows','10') + '&'
        #page ='page=' + getattr(self,'page','1') + '&'
        #postStocks = size + page + 'period='
        fileMode =getattr(self,'fileMode',False)

        self.products = re.findall(r"[\w']+", strProducts)
        url = target_url
        if beerMode:
            url = url + 'Filtro=C2596_C2598&'

        for product in  self.products:
            strSearch = 'strBusca=' + product
            self.start_urls.append(url + strSearch)
        #self.start_urls = [url]
        self.fileMode = fileMode
        self.currentPage = 0

    def parse(self, response):
        print ('SYSversion = ' + str(sys.version))
        #check python version
        if sys.version_info >= (3,6):
            urlParams = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(response.url).query))
        else:
            print('parse != 3,6' + '\n')
            from urlparse import parse_qs, urlparse
            urlParams = dict(parse_qs(urlparse(response.url).query))

        curProduct = urlParams['strBusca']

        try:
            self.currentPage = urlParams['paginaAtual']
        except Exception:
            self.currentPage = int(self.currentPage + 1)

        if self.fileMode:
            #outFilename = (curProduct + "_Page"+str(self.currentPage)+"_" + str(datetime.date.today()) + ".txt")
            outFilename = (curProduct+ '_' + str(datetime.date.today()) + ".txt")
            #os.remove(outFilename)
            outFile = open(outFilename, "a")

        #extracting prices
        productIds = ','.join(response.css('div.hproduct::attr(id)').extract())
        api_prodPriceUrl = 'http://preco.api-extra.com.br/V1/Produtos/PrecoVenda/?IdsProduto=' + productIds

        resp = requests.get(api_prodPriceUrl)
        if resp.status_code != 200:
            # This means something went wrong.
            raise ApiError('GET /tasks/ {}'.format(resp.status_code))
            for todo_item in resp.json():
                print('{} {}'.format(todo_item['id'], todo_item['summary']))
        json_resp = resp.json()
        dictPrices = dict()
        for dictObj in json_resp['PrecoProdutos']:
            dictPrices[str(dictObj['PrecoVenda']['IdProduto'])] = dictObj
        del json_resp
        del resp

        #for product in response.css('//div[@class="hproduct"]'):
        for product in response.css('div.hproduct'):
            productId = product.css('::attr(id)').extract_first()
            #price = dictPrices[productId]['PrecoVenda']['Preco']
            productDict = {
                'Name': product.css('a.link.url::attr(title)').extract_first(),
                'Id': productId,
                'Link': product.css('a.link.url::attr(href)').extract_first(),
                #'Price': price,
            }
            yield productDict
            if self.fileMode:
                outFile.write(str(productDict) + '\n')

        if self.fileMode:
            outFile.close()
        next_page = response.css('li.next a::attr(href)').extract_first()
        #proximaPagina
        if next_page is not None:
            next_page = response.urljoin(next_page)
            #yield scrapy.Request(next_page, callback=self.parse)
            yield scrapy.Request(next_page, callback=self.parse)
