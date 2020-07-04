import json
import requests
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pandas as pd

from bs4 import BeautifulSoup

#Getting the PE, EPS
def getYahooPage(stock, page):
  url_base_general = "https://finance.yahoo.com/quote/"
  url_add_pattern = "{s}/{p}?p={s}"
  url_final = url_base_general + url_add_pattern.replace("{s}",stock).replace("{p}",page)

  print("-> URL final:", url_final)

  #Trailing PE uses earnings per share of the company over the period of previous 12 months
  #Forward PE uses the forecasted earnings per share of the company over the period of next 12 months
    
  financials = {"sticker": stock}
  #response = requests.get(url_final, timeout=20)

  #if response.status_code == 200:
    #print("Rresp:",response.content.decode('utf-8'))
  
  try:
    req = Request(url_final, headers={'User-Agent': 'Mozilla/5.0'})
    fpage = urlopen(req).read().decode('utf-8')

    #dump to file to inspect
    with open("yahoo_page_dump.html", 'w', encoding="utf-8") as out:
      out.write(fpage)

    page_content = BeautifulSoup(fpage, "html.parser")
    metrics = {}

    #get title - for ETFS
    if page == "holdings":
      isFund = page_content.find("span", string="Overall Portfolio Composition (%)")
      #print("isETF:", isFund)
      if isFund != None:
        financials['type'] = 'ETF'
        metrics = { "price_earning": {"name":"Price/Earnings", "type":"float"}, 
                    "price_book": {"name":"Price/Book", "type":"float"}, 
                    "price_sales": {"name":"Price/Sales", "type":"float"}, 
                    "price_cashflow": {"name":"Price/Cashflow", "type":"float"}, 
                    "med_marketcap": {"name":"Median Market Cap", "type":"float"}, 
                    "3y_earnings_growth": {"name":"3 Year Earnings Growth", "type":"float"}, 

                    #"basic_materials": {"name":"Basic Materials", "type":"float"}, 
                  }
      else:
        financials['type'] = 'IND'

    if page == "key-statistics":
      metrics = { "trailing_pe": {"name":"Trailing P/E", "type":"float"}, 
                  "forward_pe": {"name":"Forward P/E", "type":"float"},
                  "forward_dividend_yield": {"name":"Forward Annual Dividend Yield", "type":"string"},
                  "market_cap": {"name":"Market Cap (intraday)", "type":"float"},
      
                  "eps": {"name":"Diluted EPS", "type":"float"},
                  "cps": {"name":"Total Cash Per Share", "type":"float"},

                  "cash": {"name":"Total Cash", "type":"float"},
                  "debt": {"name":"Total Debt", "type":"float"},
                  "n_shares": {"name":"Shares Outstanding", "type":"float"},
                  
                  "50_day_moving_avg": {"name":"50-Day Moving Average", "type":"string"},
                  "200_day_moving_avg": {"name":"200-Day Moving Average", "type":"string"}
                }
    elif page == "analysis":
      metrics = { 
        "annual_growth": {"name":"Next 5 Years (per annum)", "type":"string"}, 
      }
    elif page == "":
      metrics = { 
        "market_cap": {"name":"Market Cap", "type":"string"}, 
      }
      
    for key, value in metrics.items():
      title = page_content.find("span", string=value['name'])
      
      num = None
      if title != None:
        try:
          txt_value = ''
          if title.parent.nextSibling != None:
            txt_value = title.parent.nextSibling.text
          
          if page == "holdings":
            txt_value = title.parent.find_all("span")[3].text
          if value['type'] == "float":
            #k
            is_k = txt_value.find('k')
            if is_k != -1:
              num = float(txt_value.replace('k',''))
              num = num*1000
            #T
            is_t = txt_value.find('T')
            #print("Num for ",key," is B:", txt_value.replace('B',''))
            if is_t != -1:
              num = float(txt_value.replace('T',''))
              num = num*1000000000000
            #B
            is_b = txt_value.find('B')
            #print("Num for ",key," is B:", txt_value.replace('B',''))
            if is_b != -1:
              num = float(txt_value.replace('B',''))
              num = num*1000000000
            #M
            is_m = txt_value.find('M')
            if is_m != -1:
              num = float(txt_value.replace('M',''))
              num = num*1000000

            if num == None:
              num = float(txt_value.replace(",",""))

          elif value['type'] == "string":
            num = str(txt_value)
        except (ValueError, TypeError):
          print("Not a number:", key," -> ",txt_value)
      else:
        print("Not found:", key)

      financials[key] = num
    
  except HTTPError:
    print("{} - not found".format(url_final))

  return financials


def getYahooFinancials(stock):
  #print("Getting financial info for: "+str(stock))

  #https://finance.yahoo.com/quote/AAPL/?p=AAPL
  yMain = getYahooPage(stock, "holdings")
  if yMain['type'] != "ETF":
    yFinancials = getYahooPage(stock, "key-statistics")
    yAnalysis = getYahooPage(stock, "analysis")
    yFront = getYahooPage(stock, "")

    for key, value in yFinancials.items():
      if key not in yMain or yMain[key] == None:
        yMain[key] = value

    for key, value in yAnalysis.items():
      if key not in yMain or yMain[key] == None:
        yMain[key] = value

    for key, value in yFront.items():
      if key not in yMain or yMain[key] == None:
        yMain[key] = value

  return yMain

def compactNumber(num):
  num_txt = num

  if num != None:
    try:
      num = float(num)
      if num > 1000000000000:
        num_txt = str(num/1000000000000.0) + "T"
      elif num > 1000000000:
        num_txt = str(num/1000000000.0) + "B"
      elif num > 1000000:
        num_txt = str(num/1000000.0) + "M"
      elif num > 1000:
        num_txt = str(num/100.0) + "k"
    except ValueError:
      pass

  return num_txt


if __name__ == "__main__":
    print("Trying to scrape yahoo finance ...")
    
    yData = getYahooFinancials("MSFT")
    
    for key, value in yData.items():
      print(key, " -> ", value)

    #print(yData)

    print("MCap:", compactNumber(yData['market_cap']))
    print("Cash/Stock:", round(yData['cash']/yData['n_shares'],2) )
    print("Debt/Stock:", round(yData['debt']/yData['n_shares'],2))
    print("NetCash/Stock:", round((yData['cash'] - yData['debt'])/yData['n_shares'],2))



    df_yh = pd.DataFrame()
    df_yh = df_yh.append(yData, ignore_index=True)
    print(df_yh.columns)
    print(df_yh)

    