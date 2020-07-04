
import json
import requests
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd

from bs4 import BeautifulSoup

def getFinviz(stock):
  url_base = "https://finviz.com/quote.ashx?t="
  url_full = url_base + stock

  stock_data = {'ticker':stock}

  try:
    #fpage = requests.get(url)
    #https://stackoverflow.com/questions/16627227/http-error-403-in-python-3-web-scraping
    req = Request(url_full, headers={'User-Agent': 'Mozilla/5.0'})
    fpage = urlopen(req).read().decode('utf-8')

    fsoup = BeautifulSoup(fpage, 'html.parser')

    title_table = fsoup.find("table", {'class':'fullview-title'})
    #print("Title table:", title_table)
    td_tags = title_table.find_all("td")
    #print("TD tags:", td_tags)
    if len(td_tags) == 3:
      exchange = (td_tags[0]).find('span').text
      #print("Exchange:", exchange.strip('[]'))
      stock_data['exchange'] = exchange.strip('[]')

      classification = (td_tags[2]).find_all('a')
      #print("Industry:", classification[0].text)
      #print("Sector:", classification[1].text)
      stock_data['industry'] = classification[0].text
      stock_data['sector'] = classification[1].text


    h_tags = fsoup.find_all('td', {'class':'snapshot-td2-cp'})
    v_tags = fsoup.find_all('td', {'class':'snapshot-td2'})
    for htag, vtag in zip(h_tags, v_tags):
      #print("Vatg:",vtag)
      stock_data[htag.text] = vtag.text
  
  except HTTPError:
    print("{} - not found".format(url_full))

  return stock_data



if __name__ == "__main__":
    print("Trying to scrape finviz finance ...")

    yMain = getFinviz('MSFT')
    for t, v in yMain.items():
      print(t, " -> ", v)

    df_fv = pd.DataFrame()
    df_fv = df_fv.append(yMain, ignore_index=True)
    print(df_fv)