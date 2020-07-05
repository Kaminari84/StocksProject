import csv
import requests
import pandas as pd
import numpy as np
import time
import pytz
import datetime as dt
from pytz import timezone
from pytz import common_timezones
from pytz import country_timezones

from urllib.error import HTTPError
from urllib.request import Request, urlopen
import pandas_datareader.data as web
from bs4 import BeautifulSoup

#Date-Time helpers
def utcnow():
    return dt.datetime.now(tz=pytz.utc)

def pstnow():
    utc_time = utcnow()
    pacific = timezone('US/Pacific')
    pst_time = utc_time.astimezone(pacific)
    return pst_time

def getDividendData(stock):
  url_base = "https://finviz.com/quote.ashx?t="
  url_full = url_base + stock

  stock_data = {'ticker':stock}

  try:
    #fpage = requests.get(url)
    #https://stackoverflow.com/questions/16627227/http-error-403-in-python-3-web-scraping
    req = Request(url_full, headers={'User-Agent': 'Mozilla/5.0'})
    fpage = urlopen(req).read().decode('utf-8')

    fsoup = BeautifulSoup(fpage, 'html.parser')

    #Grt top table title, industry
    title_table = fsoup.find("table", {'class':'fullview-title'})
    #print("Title table:", title_table)
    td_tags = title_table.find_all("td")

    #print("TD tags:", td_tags)
    if len(td_tags) == 3:
      exchange = (td_tags[0]).find('span').text
      #print("Exchange:", exchange.strip('[]'))
      stock_data['exchange'] = exchange.strip('[]')

      full_name = (td_tags[1]).text
      stype = 'IND'
      if "ETF" in full_name:
        stype = "ETF"
      elif "REIT" in full_name:
        stype = "REIT"

      stock_data['type'] = stype
      stock_data['full_name'] = full_name

      classification = (td_tags[2]).find_all('a')
      #print("Industry:", classification[0].text)
      #print("Sector:", classification[1].text)
      stock_data['industry'] = classification[0].text
      stock_data['sector'] = classification[1].text

    #Get all main table stats
    h_tags = fsoup.find_all('td', {'class':'snapshot-td2-cp'})
    v_tags = fsoup.find_all('td', {'class':'snapshot-td2'})
    for htag, vtag in zip(h_tags, v_tags):
      #print("Vatg:",vtag)
      stock_data[htag.text] = vtag.text
  
  except HTTPError:
    print("{} - not found".format(url_full))

  return stock_data

#Get the stock prices historical
def getStockPrices(stock, start, end):
  df = web.DataReader(stock, 'yahoo', start, end)

  return df

'''
url_base = "https://finviz.com/quote.ashx?t="
tckr = ['SBUX','MSFT','AAPL']
url_list = [url_base + s for s in tckr]

with open('./SO.csv', 'a', newline='') as f:
    writer = csv.writer(f)

    for url in url_list:
        try:
            #fpage = requests.get(url)
            #https://stackoverflow.com/questions/16627227/http-error-403-in-python-3-web-scraping
            req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            fpage = urlopen(req).read().decode('utf-8')

            with open("./finviz_dividend.html", 'w') as out:
              out.write(fpage)
              #out.write(fpage.content.decode('utf-8').replace("\n"," "))
              
            
            fsoup = BeautifulSoup(fpage, 'html.parser')

            #e = fsoup.find_all('td', {'class':'snapshot-td2-cp'})
            #print("E:",e)

            
            # write header row
            writer.writerow(map(lambda e : e.text, fsoup.find_all('td', {'class':'snapshot-td2-cp'})))

            # write body row
            writer.writerow(map(lambda e : e.text, fsoup.find_all('td', {'class':'snapshot-td2'})))   
                 
        except HTTPError:
            print("{} - not found".format(url))
'''


if __name__ == "__main__":
  tickers = ['PFLT','HRZN','PBT','LEG','T','KHC','ABBV','MMM',
            'MRK','HD','VFC','TXN','NBTB','CL','PCLB','MCD','LMT','ADP',
            'BMO','BCE','IBM','CAH','HPQ','AVGO','WHR','PEP','NEE','WM',
            'JNJ','VZ','HRL','GE','XOM','DIS','DON','DOO','BDCS','CMA',
            'QCOM','DVN','IRM','JCI','PXD','HUN','JEF',
            'OMF','TCF','TRN','WBS','SQM','BBL','BHP','ENIC','EPD',
            'FL','HBI','HRB','IPG','LYB','PAC','PM','PSXP','RIO','TCP',
            'TKC','TOT','WYND','ASR','BKE','BSM','CAMT','CANG','CODI','CPA',
            'CPAC','DBI','DHT','EBF','FANH','GES','GILT','GSH','HNI','HVT',
            'KRO','MED','MSM','PFE','PSO','RGP','RMR','SCHN','SKM','SOI',
            'UVV','WDR','SO','AWK','BIP','BIPC','TRP','AMKBY','MARUY',
            'MFG','MZHOF','PSX','VLO','MPC','PII','D','FTAI','MCY',
            #ETFS - https://finviz.com/screener.ashx?v=111&f=ind_exchangetradedfund
            'QQQ','SKYY','SPHD','VNQ','AMLP','BND','DVY','VXUS','VTV','DWX',
            'VYM','VYMI','VTI','VOO','SPY','VOOG','VOOV','SPYD','HYLD','ARKK',
            "ARKW",'ARKG','ARKQ','ARKF','USHY','QYLD','NOBL','SDEM','SRET',
            'TLT','VGT','CLIX','CWEB','DGAZ','FNGO','FNGU','KOLD','OGIG',
            'TMF','VIIX','VIXM','VIXY','VXX','VXZ','XVZ',
            #REIT - office - https://finviz.com/screener.ashx?v=111&f=ind_reitoffice&t=
            'AAT','COR','DLR','DEI','ARE','BDN','BXP','CIO','CLI','CMCT','CUZ',
            'CXP','DEA','EQC','FSP','GNL','HIW','HPP','JBGS','KRC','OFC','OPI',
            'PDM','PGRE','PSTL','SLG','VNO','WRE',
            #REIT - specialty - https://finviz.com/screener.ashx?v=141&f=ind_reitspecialty
            'AMT','CCI','CONE','CTT','CXW',
            #REIT - residential
            'ACC',
            #REIT - diversified
            'SRC',
            #REIT - industrial
            'PLD',
            #REIT - retail
            'SPG','WRI','EPR','O',
            #REIT - Healthcare Facilities
            'WELL',
            #REIT - mortgage
            'NRZ'
            ]

  df = pd.DataFrame({})
  for index, tckr in enumerate(tickers):
    print("\n*** At",tckr,":", index,"of",len(tickers),"***")

    sdata = getDividendData(tckr)
    
    start = dt.datetime(2010,1,1)
    end = dt.datetime.now() #dt.datetime(2020,5,27)

    df_price = getStockPrices(tckr, start, end)
    #print("Cols:", df_price.columns)
    curr_price = df_price['Close'].sort_index(ascending=True).tail(1).mean()
    #print("Curr price:", curr_price)

    #Get price at the bginning of the year
    beg_year = dt.datetime(dt.datetime.now().year,1,1)
    beg_year_price = df_price[(df_price.index >= beg_year)]['Close'].sort_index(ascending=True).head(5).mean()
    #print(df_price[(df_price.index >= beg_year)]['Close'].sort_index(ascending=True).head(5))
    #print("Beg year price:", beg_year_price)

    #Get price last year
    past_1y = dt.datetime.now() - dt.timedelta(days=365)
    past_1y_price = df_price[(df_price.index >= past_1y)]['Close'].sort_index(ascending=True).head(10).mean()
    #print(df_price[(df_price.index >= past_1y)]['Close'].sort_index(ascending=True).head(10))
    #print("Last 1 year price:", past_1y_price)

    #Get price 2 years ago
    past_2y = dt.datetime.now() - dt.timedelta(days=365*2)
    past_2y_price = df_price[(df_price.index >= past_2y)]['Close'].sort_index(ascending=True).head(15).mean()
    #print("Last 2 year price:", past_2y_price)

    #Get price 5 years ago
    past_5y = dt.datetime.now() - dt.timedelta(days=365*5)
    past_5y_price = df_price[(df_price.index >= past_5y)]['Close'].sort_index(ascending=True).head(20).mean()
    #print("Last 5 year price:", past_5y_price)

    #Get price 10 years ago
    past_10y = dt.datetime.now() - dt.timedelta(days=365*10)
    past_10y_price = df_price[(df_price.index >= past_10y)]['Close'].sort_index(ascending=True).head(30).mean()
    #print("Last 10 year price:", past_10y_price)

    sdata['c_price'] = curr_price
    sdata['by_price'] = beg_year_price
    sdata['1y_price'] = past_1y_price
    sdata['2y_price'] = past_2y_price
    sdata['5y_price'] = past_5y_price
    sdata['10y_price'] = past_10y_price
    sdata['perf_YTD'] = (curr_price - beg_year_price)*100.0/curr_price
    sdata['perf_y1'] = (curr_price - past_1y_price)*100.0/curr_price
    sdata['perf_y2'] = (curr_price - past_2y_price)*100.0/curr_price
    sdata['perf_y5'] = (curr_price - past_5y_price)*100.0/curr_price
    sdata['perf_y10'] = (curr_price - past_10y_price)*100.0/curr_price

    df = df.append(sdata, ignore_index=True)

    sel_cols = ['ticker', 'full_name', 'type', 'industry', 'sector', 
                'Price','Dividend %','Payout','perf_YTD', 'perf_y1', 
                'perf_y2', 'perf_y5', 'perf_y10',
                'Perf YTD','Perf Year','Current Ratio','Debt/Eq','LT Debt/Eq','Market Cap',
                'c_price','by_price','1y_price','2y_price','5y_price','10y_price']

    print(df[-1:][sel_cols])

    dt_str = pstnow().strftime('%d_%m_%Y')
    filename_short = "dividend_data/_dividend_stock_"+str(dt_str)+".csv" 
    filename_full = "dividend_data/dividend_stock_"+str(dt_str)+".csv"
    #print("Filename:", filename)
    df[sel_cols].to_csv(filename_short, float_format='%.2f', index = None, header=True)
    df.to_csv(filename_full, float_format='%.2f', index = None, header=True)

  print(df.columns)
  print(df[['ticker', 'full_name', 'type', 'industry', 'sector', 'Price','Dividend %','Payout',
            'perf_YTD', 'perf_y1', 'perf_y2', 'perf_y5', 'perf_y10']])
             #'c_price','by_price','1y_price','2y_price','5y_price','10y_price']])
            
  print("Saved to:", filename_short)
           