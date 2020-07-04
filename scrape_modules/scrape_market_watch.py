import json
import requests
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd

from bs4 import BeautifulSoup

#Getting the PE, EPS
def getMarketWatch(stock, page):
  url_base_general = "https://www.marketwatch.com/investing/stock/"
  url_add_pattern = "{s}/{p}"
  url_final = url_base_general + url_add_pattern.replace("{s}",stock).replace("{p}",page)

  print("-> URL final:", url_final)

  financials = {"sticker": stock}

  try:
    #response = requests.get(url_final, timeout=20)
    req = Request(url_final, headers={'User-Agent': 'Mozilla/5.0'})
    fpage = urlopen(req).read().decode('utf-8')

    #dump to file to inspect
    with open("market_watch_page_dump.html", 'w', encoding="utf-8") as out:
      out.write(fpage)

    fsoup = BeautifulSoup(fpage, 'html.parser')

    financials = {}

    h_tag = fsoup.find('tr', {'class':'topRow'})
    y_tags = h_tag.find_all('th', {'scope':"col"})
    print("y tags:", y_tags[0:-1])

    #add years
    financials['stock'] = [stock for s in range(len(y_tags)-1)]
    financials['years'] = [y.text for y in y_tags[0:-1]]

    #rows
    r_tags = fsoup.find_all('td', {'class':'rowTitle'})
    n = 15
    for r_tag in r_tags:
      v_tags = r_tag.parent.find_all('td', {'class':'valueCell'})

      financials[r_tag.text.strip()] = [v.text for v in v_tags]

      n-=1
      if n==0:
        break

  except HTTPError:
    print("{} - not found".format(url_final))

  return financials


if __name__ == "__main__":
    print("Trying to scrape market watch finance ...")

    yMain = getMarketWatch('MSFT', 'financials')
    for t, v in yMain.items():
      print(t, " -> ", v)

    df_mw = pd.DataFrame(yMain)
    print(df_mw)