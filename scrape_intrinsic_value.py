import json
import requests
import time
import pytz
import datetime as dt
from pytz import timezone
from pytz import common_timezones
from pytz import country_timezones

import pandas as pd
import numpy as np
import os.path
import random

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

#Getting the PE, EPS
def getYahooFinancials(stock, page):
  url_base_general = "https://finance.yahoo.com/quote/"
  url_add_pattern = "{s}/{p}?p={s}"
  url_final = url_base_general + url_add_pattern.replace("{s}",stock).replace("{p}",page)

  #print("-> URL final:", url_final)

  #Trailing PE uses earnings per share of the company over the period of previous 12 months
  #Forward PE uses the forecasted earnings per share of the company over the period of next 12 months
    
  financials = {"sticker": stock}

  response = requests.get(url_final, timeout=20)
  if response.status_code == 200:
    #print("Rresp:",response.content.decode('utf-8'))
    page_content = BeautifulSoup(response.content, "html.parser")

    metrics = {}
    if page == "key-statistics":
      metrics = { "trailing_pe": {"name":"Trailing P/E", "type":"float"}, 
                  "forward_pe": {"name":"Forward P/E", "type":"float"},
                  "peg_ratio": {"name":"PEG Ratio (5 yr expected)", "type":"float"},
                  "price_sales": {"name":"Price/Sales", "type":"float"},
                  "price_book": {"name":"Price/Book", "type":"float"},
                  "ev_rev": {"name":"Enterprise Value/Revenue", "type":"float"},
                  #"market_cap": {"name":"Market Cap (intraday)", "type":"float"},
                  
                  "forward_dividend_yield": {"name":"Forward Annual Dividend Yield", "type":"string"},
                  "q_revenue_growth": {"name":"Quarterly Revenue Growth", "type":"string"},
                  "q_earnings_growth": {"name":"Quarterly Earnings Growth", "type":"string"},
      
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
        "market_cap": {"name":"Market Cap", "type":"float"}, 
        "trailing_pe": {"name":"PE Ratio (TTM)", "type":"float"}, 
        "eps": {"name":"EPS (TTM)", "type":"float"}, 
      }
      
    for key, value in metrics.items():
      title = page_content.find("span", string=value['name'])
      
      num = None
      if title != None:
        try:
          txt_value = ''
          if title.parent.nextSibling != None:
            txt_value = title.parent.nextSibling.text
            #if txt_value == "N/A":
            #  #print("K:", key, "IS ---> N/A")
            #  if title.parent.nextSibling.nextSibling != None:
            #    txt_value = title.parent.nextSibling.nextSibling.text


          if value['type'] == "float":
            #k
            is_k = txt_value.find('k')
            if is_k != -1:
              num = float(txt_value.replace('k','').replace(",",""))
              num = num*1000
            #T
            is_t = txt_value.find('T')
            #print("Num for ",key," is B:", txt_value.replace('B',''))
            if is_t != -1:
              num = float(txt_value.replace('T','').replace(",",""))
              num = num*1000000000000
            #B
            is_b = txt_value.find('B')
            #print("Num for ",key," is B:", txt_value.replace('B',''))
            if is_b != -1:
              #print("MCAP clean:", txt_value.replace('B','').replace(",",""))
              num = float(txt_value.replace('B','').replace(",",""))
              num = num*1000000000
            #M
            is_m = txt_value.find('M')
            if is_m != -1:
              num = float(txt_value.replace('M','').replace(",",""))
              num = num*1000000

            if num == None:
              num = float(txt_value.replace(",",""))

          elif value['type'] == "string":
            num = str(title.parent.nextSibling.text)
        
          #fff
          if key in ["peg_ratio","price_sales","price_book","ev_rev","market_cap"]:
            print("T:", key, " -> ", num, ", RAW:", txt_value)

        except (ValueError, TypeError):
          print("Not a number:", key," -> ",title.parent.nextSibling.text)
      else:
        print("Not found:", key)

      financials[key] = num

  return financials


def getMSNMoneyFinancials(stock, page):
  url_base_general = "https://www.msn.com/en-us/money/stockdetails/"
  url_add_pattern = "{p}/?symbol={s}&form=PRFIEQ"
  url_final = url_base_general + url_add_pattern.replace("{s}",stock).replace("{p}",page)

  #print("-> MSN Money URL final:", url_final)

  financials = {"sticker": stock}

  response = requests.get(url_final, timeout=20)
  if response.status_code == 200:
    #print("Rresp:",response.content.decode('utf-8'))
    #with open("msn_money_wb.html", 'w') as out:
    #  out.write(response.content.decode('utf-8'))

    page_content = BeautifulSoup(response.content, "lxml")
    #page_content.prettify()

    current_price = page_content.find("span", {"data-role":"currentvalue"})
    #print("Current price:"+str(current_price.text))
    if current_price:
      financials['current_price'] = current_price.text

    #AFTER HOURS
    after_hours_container = page_content.find(class_="precurrentvalue")
    after_hours_price = after_hours_container.find("span", class_="currentval")
    #print("After hours price:"+str(after_hours_price.text))
    financials['post_price'] = after_hours_price.text

    metrics = { 
      "high_5y_pe": {"name":"P/E Ratio 5-Year High", "type":"float"}, 
      "low_5y_pe": {"name":"P/E Ratio 5-Year Low", "type":"float"}, 
    }
      
    for key, value in metrics.items():
      val_container = page_content.find(string=value['name'])
      val_text = None
      if val_container != None:
        val_elem = val_container.parent.parent.parent.next_sibling.next_sibling
        val_text = val_elem.find("p", class_="truncated-string")
      
      num = None 
      if val_text != None:
        try:
          num = float(val_text.text)
        except (ValueError, TypeError):
          num = None
      
      financials[key] = num

    #No past PE ratio available
    if financials[list(metrics.keys())[0]] == None:
      url_base_general = "https://www.msn.com/en-us/money/stockdetails/"
      url_add_pattern = "/?symbol={s}&form=PRFIEQ"
      url_final = url_base_general + url_add_pattern.replace("{s}",stock).replace("{p}",page)

      print("-> MSN Money URL backup:", url_final)

      response = requests.get(url_final, timeout=20)
      if response.status_code == 200:
        #print("Rresp:",response.content.decode('utf-8'))
        #with open("msn_money_wb_main.html", 'w') as out:
        #  out.write(response.content.decode('utf-8'))

        page_content = BeautifulSoup(response.content, "lxml")
        #page_content.prettify()

        current_pe = page_content.find("p", {"title":"P/E Ratio (EPS)"})
        #print("Current price:"+str(current_price.text))
        if current_pe:
          pe_entry_li = current_pe.parent
          #print("C-P/E:"+str(pe_entry_li))

          pe_val_elem = pe_entry_li.next_sibling.next_sibling
          if pe_val_elem != None:
            print("P/E val elem:"+str(pe_val_elem))
            pe_val = pe_val_elem.text[0:pe_val_elem.text.find('(')]
            num = None 
            if pe_val != None:
              try:
                num = float(pe_val)
              except (ValueError, TypeError):
                num = None
            print("P/E val:"+str(num))

            for key, value in metrics.items():
              financials[key] = num
  return financials

#Get the stock prices historical
def getStockPrices(stock, start, end):
  #url_base_general = "https://finance.yahoo.com/"
  #url_add_pattern = "{p}/{s}/history?period1=511056000&period2=1584921600&interval=1mo&filter=history&frequency=1mo"
  #url_final = url_base_general + url_add_pattern.replace("{s}",stock).replace("{p}",page)

  df = web.DataReader(stock, 'yahoo', start, end)

  return df

  #super simple price get -> https://www.youtube.com/watch?v=2BrpKpWwT2As

  #print("-> URL final:", url_final)
  #https://finance.yahoo.com/quote/MSFT/history?period1=511056000&period2=1584921600&interval=1mo&filter=history&frequency=1mo
  #https://finance.yahoo.com/history/MSFT/history?period1=511056000&period2=1584921600&interval=1mo&filter=history&frequency=1mo
  #https://finance.yahoo.com/quote/MSFT/history?period1=511056000&period2=1584921600&interval=1mo&filter=history&frequency=1mo

  #Historic EPS: https://ycharts.com/companies/MSFT/eps_ttm 

  '''
  quotes = {}

  response = requests.get(url_final, timeout=10)
  if response.status_code == 200:
    #print("Rresp:",response.content.decode('utf-8'))
    page_content = BeautifulSoup(response.content, "html.parser")

    data_table = page_content.find("table", {"data-test": "historical-prices"})
    data_head = data_table.find("thead")

    print("data head:"+str(data_head))
  '''

  #table
  #data-test="historical-prices"

  return None



def calcIntrinsicValue(eps, growth, dividend, min_return, safety_margin, forward_pe, years):
  eps_future = 0
  stock_price_future = 0
  try:
    eps_future = eps*(1.0+growth)**(years-1)
    stock_price_future = eps_future*forward_pe
  except (ValueError, TypeError):
    print("ERROR, cound not calculate future price -> EPS: "+str(eps)+", Growth: "+str(growth)+", Forward P/E: "+str(forward_pe))

  #this is based on expected return
  stock_fair_value = stock_price_future/(1+min_return-dividend)**(years-1)

  #buy value based on safty margin
  buy_stock_price = stock_fair_value*safety_margin

  return eps_future, stock_price_future, stock_fair_value, buy_stock_price


def getCurrentFinancialInfo(stock):
  #print("Getting financial info for: "+str(stock))
  # + PE ratio
  # + EPS or number shares outstanding+revenue
  # + Growth rate estimates
  # + Dividend

  #https://finance.yahoo.com/quote/AAPL/?p=AAPL
  yMain = {}
  yFinancials = getYahooFinancials(stock, "key-statistics")
  yAnalysis = getYahooFinancials(stock, "analysis")
  yFront = getYahooFinancials(stock, "")

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


  yInfo = getCurrentFinancialInfo('MSFT') #NOK #WB #TRUP #SHOP
  msnInfo = getMSNMoneyFinancials('MSFT',"analysis") 
  for key, value in msnInfo.items():
    yInfo[key] = value
  print("Financial: "+str(yInfo))


  #DVN
  eps = -4.78
  growth = -2.7
  dividend = 3.58
  min_return = 0.15 # 15%
  safety_margin = 0.5 # 50%
  forward_pe = 20.39
  years = 10

  eps_future, stock_price_future, stock_fair_value, buy_stock_price = calcIntrinsicValue(eps, growth, dividend, min_return, 
              safety_margin, forward_pe, years)

  print("%s -> Curr: %s, In %i years -> eps: %.2f, stock_price: %.2f, Current -> Fair value: %.2f, buy price: %.2f" % 
      ('dvn', 12.31, years, eps_future, stock_price_future, stock_fair_value, buy_stock_price))

  df_hld = pd.read_json (r'rbh_holdings.json').transpose()
  print (df_hld)


  ans = input("Continue?")

  #50 MarkCap - http://www.iweblists.com/us/commerce/MarketCapitalization.html
  #Unicorns - https://www.cbinsights.com/research-unicorn-companies
  #https://en.wikipedia.org/wiki/List_of_S%26P_500_companies
  #https://en.wikipedia.org/wiki/S%26P_600
  #https://en.wikipedia.org/wiki/S%26P_1500
  #https://en.wikipedia.org/wiki/List_of_S%26P_1000_companies
  stocks = ['AAPL', 'NVDA', 'AMD', 'MSFT', 'AMZN', 'CSCO', 'INTC', 'ETSY', 'ZNGA', 'KO', 'KR', 'DIS', 
            'SBUX', 'NFLX', 'VMW', 'TCEHY', 'ON', 'JPM', 'ADSK', 'GOOGL', 'SQ', 'BA', 'PYPL', 'FB', 
            'BIDU', 'TWTR', 'ADBE', 'TXN', 'V', 'UNH', 'NOC', 'LMT', 'EBAY', 'TTWO', 'BLK', 
            'ATVI', 'COST', 'BIIB', 'BAC', 'OXY', 'RH', 'SU', 'GM', 'AXP', 
            'KHC', 'USB', 'MCO', 'STKS', 'JNJ', 'GILD', 'RNG', 'TTD', 'PEP',
            'T', 'DUK', 'SIRI', 'SSRM', 'BMY', 'CLDT','MMM', 'VZ', 'ABBV', 
            'NRZ', 'DAL', 'GE', 'PFE', 'SNE', 'NKE', 'WMT', 'RTN', 
            'WB', 'SHOP', 'PM', 'WPC', 'MRK', 'MDT', 'HD', 'TROW', 'AFL', 
            'DX', 'TWO', 'AGNC', 'COKE', 'HPQ', 'BBY', 'ZBRA', 'HUM', 'LOGI', 
            'VFC', 'LIT', 'ALGN', 'SWKS', 'SPXC', 'LRCX', 'MSCI', 'JD', 'ISRG', 
            'MTN', 'GD', 'GS', 'AMP', 'SYF', 'LDOS', 'HII', 'STM', 'WYNN', 
            'MA', 'WYND', 'MAR', 'HLT', 'PKI', 'HIMX', 'CAT', 'BBN',
            'BLK', 'SENS', 'BKNG', 'F', 'NXPI', 'LITE', 'PAAS', 'Z', 'EA',
            'ADP', 'NEM', 'G', 'TSM', 'NVS', 'RHHBY', 'NSRGY', 'NOK', 'QCOM',
            'OHI', 'CGC', 'CVS', 'EAF', 'WWR', 'BBU', 'BATT', 'C', 'PETS', 
            'CLDT', 'MCD', 'ACN', 'O', 'SFTBY', 'ZM', 'TRUP', 'ABT', 'ABMD', 
            'ACN', 'AAP', 'AES', 'A', 'APD', 'AKAM', 'ALK', 'ALB', 'ARE', 
            'ALXN', 'ALLE', 'AGN', 'ADS', 'LNT', 'ALL', 'GOOG', 'MO', 'AMCR', 
            'AEE', 'AAL', 'AEP', 'AIG', 'AMT', 'AWK', 'ABC', 'AME', 'AMGN', 
            'APH', 'ADI', 'ANSS', 'ANTM', 'AON', 'APA', 'AIV', 'AMAT', 'APTV', 
            'ADM', 'ANET', 'AJG', 'AIZ', 'ATO', 'AZO', 'AVB', 'AVY', 'BKR', 
            'BLL', 'BK', 'BAX', 'BDX', 'BRKB', 'BWA', 'BXP', 'BSX', 
            'AVGO', 'BR', 'BFB', 'CHRW', 'COG', 'CDNS', 'CPB', 'COF', 'CPRI', 
            'CAH', 'KMX', 'CCL', 'CARR', 'CAT', 'CBOE', 'CBRE', 'CDW', 'CE', 
            'CNC', 'CNP', 'CTL', 'CERN', 'CF', 'SCHW', 'CHTR', 'CVX', 'CMG', 
            'CB', 'CHD', 'CI', 'CINF', 'CTAS', 'C', 'CFG', 'CTXS', 'CLX', 
            'CME', 'CMS', 'CTSH', 'CL', 'CMCSA', 'CMA', 'CAG', 'CXO', 'COP', 
            'ED', 'STZ', 'COO', 'CPRT', 'GLW', 'CTVA', 'COTY', 'CCI', 'CSX', 
            'CMI', 'DHI', 'DHR', 'DRI', 'DVA', 'DE', 'DAL', 'XRAY', 'DVN', 
            'FANG', 'DLR', 'DFS', 'DISCA', 'DISCK', 'DISH', 'DG', 'DLTR', 
            'D', 'DOV', 'DOW', 'DTE', 'DRE', 'DD', 'DXC', 'ETFC', 'EMN', 
            'ETN', 'EBAY', 'ECL', 'EIX', 'EW', 'EA', 'EMR', 'ETR', 'EOG', 
            'EFX', 'EQIX', 'EQR', 'ESS', 'EL', 'EVRG', 'ES', 'RE', 'EXC', 
            'EXPE', 'EXPD', 'EXR', 'XOM', 'FFIV', 'FAST', 'FRT', 'FDX', 
            'FIS', 'FITB', 'FE', 'FRC', 'FISV', 'FLT', 'FLIR', 'FLS', 'FMC', 
            'F', 'FTNT', 'FTV', 'FBHS', 'FOXA', 'FOX', 'BEN', 'FCX', 'GPS', 
            'GRMN', 'IT', 'GE', 'GIS', 'GM', 'GPC', 'GILD', 'GL', 'GPN', 
            'GS', 'GWW', 'HRB', 'HAL', 'HBI', 'HOG', 'HIG', 'HAS', 'HCA', 
            'PEAK', 'HP', 'HSIC', 'HSY', 'HES', 'HPE', 'HLT', 'HFC', 'HOLX', 
            'HD', 'HON', 'HRL', 'HST', 'HWM', 'HUM', 'HBAN',
            'IEX', 'IDXX', 'INFO', 'ITW', 'ILMN', 'INCY', 'IR', 'ICE', 'IBM', 
            'IP', 'IPG', 'IFF', 'INTU', 'IVZ', 'IPGP', 'IQV', 'IRM', 
            'JKHY', 'J', 'JBHT', 'SJM', 'JCI', 'JNPR', 'KSU', 'K', 'KEY', 
            'KEYS', 'KMB', 'KIM', 'KMI', 'KLAC', 'KSS', 'KHC', 'KR', 'LB', 
            'LHX', 'LH', 'LW', 'LVS', 'LEG', 'LEN', 'LLY', 'LNC', 
            'LIN', 'LYV', 'LKQ', 'L', 'LOW', 'LYB', 'MTB', 'MRO', 'MPC',
            'MKTX', 'MMC', 'MLM', 'MAS', 'MKC', 'MXIM', 'MCD', 'MCK', 'MDT',
            'MRK', 'MET', 'MTD', 'MGM', 'MCHP', 'MU', 'MAA', 'NHK', 'TAP',
            'MDLZ', 'MNST', 'MCO', 'MS', 'MOS', 'MSI', 'MSCI', 'MYL', 'NDAQ',
            'NOV', 'NTAP', 'NWL', 'NWSA', 'NWS', 'NEE', 'NLSN', 'NKE',
            'NI','NBL', 'JWN', 'NSC', 'NTRS', 'NLOK', 'NCLH', 'NRG', 'NUE',
            'NVR', 'ORLY', 'ODFL', 'OMC', 'OKE', 'ORCL', 'OTIS', 'PCAR',
            'PKG', 'PH', 'PAYX', 'PAYC', 'PNR', 'PBCT', 'PKI', 'PRGO', 'PFE',
            'PSX', 'PNW', 'PXD', 'PNC', 'PPG', 'PPL', 'PFG', 'PG',
            'PGR', 'PLD', 'PRU', 'PEG', 'PSA', 'PHM', 'PVH', 'QRVO', 'PWR',
            'DGX', 'RL', 'RJF', 'RTX', 'O', 'REG', 'REGN', 'RF', 'RSG', 'RMD',
            'RHI', 'ROK', 'ROL', 'ROP', 'ROST', 'RCL', 'SPGI', 'CRM', 'SBAC',
            'SLB', 'STX', 'SEE', 'SRE', 'NOW', 'SHW', 'SPG', 'SLG',
            'SNA', 'SO', 'LUV', 'SWK', 'STT', 'STE', 'YK', 'SIVB', 'SNPS',
            'SYY', 'TMUS', 'TROW', 'TPR', 'TGT', 'TEL', 'FTI', 'TFX', 'TXT',
            'TMO', 'TIF', 'TJX', 'TSCO', 'TT', 'TDG', 'TRV', 'TFC', 'TSN',
            'UDR', 'ULTA', 'USB', 'UAA', 'UA', 'UNP', 'UAL', 'UPS', 'URI',
            'UHS', 'UNM', 'VLO', 'VAR', 'VTR', 'VRSN', 'VZ', 'VRTX',
            'VIAC', 'V', 'VNO', 'VMC', 'WRB', 'WAB', 'WMT', 'WBA', 'WM', 
            'WAT', 'WEC', 'WFC', 'WELL', 'WDC', 'WU', 'WRK', 'WY', 'WHR',
            'WMB', 'WLTW', 'XEL', 'XRX', 'XLNX', 'XYL', 'YUM',
            'ZBH', 'ZION', 'ZTS', "TWOU", "ACHC", "AYI", "ADNT", "ADT", 
            "ACM", "AMG", "AGCO", "AGIO", "AL", "AA", "ALKS", "Y", "ALSN", 
            "ALLY", "ALNY", "AMCX", "DOX", "UHAL", "ACC", "AFG", "AMH", "ANAT", 
            "NLY", "AR", "APY", "APLE", "ATR", "WTR", "ARMK", "ACGL", "ARNC", 
            "ARD", "AWI", "ARW", "ASH", "AZPN", "ASB", "AGO", "ATH", "TEAM", 
            "AN", "AGR", "AVT", "EQH", "AXTA", "AXS", "BOH", "OZK", "BKU", 
            "BERY", "BYND", "BGCP", "BMRN", "BIO", "TECH", "BKI", 
            "BLUE", "BOKF", "BAH", "BDN", "BFAM", "BHF", "BRX", "BPRN", "BRO", 
            "BFA", "BC", "BG", "BURL", "BWXT", "CABO", "CBT", "CACI", 
            "CZR", "CPT", "CMD", "CSL", "CRI", "CASY", "CTLT", "CBS", "CDK", 
            "CELG", "CDEV", "CDAY", "CRL", "CHE", "LNG", "CHK", "CIM", "CHH", 
            "XEC", "CNK", "CIT", "CLH", "CNA", "CNX", "CGNX", "COHR", "CFX", 
            "CLNY", "CXP", "COLM", "CBSH", "COMM", "CNDT", "CPA", "CLGX", "COR", 
            "OFC", "CSGP", "CR", "CACC", "CCK", "CUBE", "CFR", "CW", "CY", "CONE", 
            "SITC", "DELL", "DXCM", "DKS", "DOCU", "DLB", "DPZ", "CLR", "DEI", "DPS",
            "DNB", "DNKN", "EXP", "EWBC", "EV", "SATS", "ESRT", "EHC", "EGN", "ENR", 
            "EVHC", "EPAM", "EPR", "EQT", "EQC", "ELS", "ERIE", "EEFT", "EVR", "UFS", 
            "DCI", "STAY", "XOG", "FDS", "FICO", "FEYE", "FAF", "FCNCA", "FDC", "FHB", 
            "FHN", "FSLR", "FND", "FLO", "FLR", "FNB", "FNF", "FL", "GLPI", "EXAS", 
            "EXEL", "GTES", "GLIBA", "GWR", "GNTX", "GDDY", "GT", "GRA", "GGG", "GHC", 
            "LOPE", "GPK", "GRUB", "GWRE", "HAIN", "THG", "HE", "HCP", "HDS", "HTA", 
            "HEIA", "HEI", "HLF", "GDI", "HGV", "HPT", "HHC", "HUBB", "HPP", "HUN", 
            "H", "IAC", "ICUI", "INGR", "PODD", "IART", "IBKR", "IGT", "INVH", "IONS", 
            "HXL", "HIW", "HRC", "JAZZ", "JBGS", "JEF", "JBLU", "JLL", "KAR", "KRC", "KEX", 
            "KNX", "KOS", "LAMR", "LSTR", "LAZ", "LEA", "LM", "LEN.B", "LII", "LBRDA", "LBRDK", 
            "FWONA", "ITT", "JBL", "JEC", "LECO", "LGF-A", "LGF-B", "LFUS", "LOGM", "LPLA", 
            "LULU", "LYFT", "MAC", "MIC", "M", "MSG", "MANH", "MAN", "MKL", "MRVL", "MASI", 
            "MTCH", "MAT", "MDU", "MPW", "MD", "FWONK", "LPT", "LSXMA", "LSXMK", "LSI", "MIK", 
            "MIDD", "MKSI", "MHK", "MOH", "MPWR", "MORN", "MSM", "MUR", "NBR", "NDAQ", "NFG", 
            "NATI", "NNN", "NAVI", "NCR", "NKTR", "NBIX", "NYCB", "NEU", "MCY", "MFA", "NUS", 
            "NUAN", "NTNX", "NVT", "OGE", "OKTA", "ORI", "OLN", "OMF", "OSK", "OUT", "OC", 
            "OI", "PACW", "PANW", "PGRE", "PK", "PE", "PTEN", "NDSN", "PCG", "PPC", "PNFP", 
            "PF", "ESI", "PII", "POOL", "BPOP", "POST", "PRAH", "PINC", "PFPT", "PB", "PTC", 
            "PSTG", "QGEN", "PBF", "PEGA", "PAG", "PEN", "RLGY", "RP", "RBC", "RGA", "RS", "RNR", 
            "RPAI", "RGLD", "RES", "RPM", "RSPP", "R", "SABR", "SAGE", "SC", "SRPT", "SNDR", "SMG", 
            "SEB", "QRTEA", "RRC", "RYN", "SBNY", "SLGN", "SIX", "SKX", "SLM", "SM", "AOS", "SON", 
            "SCCO", "SPB", "SPR", "SRC", "SPLK", "S", "SFM", "SSNC", "STWD", "STLD", "SRCL", "STL", 
            "STOR", "SYK", "SUI", "STI", "SWCH", "SGEN", "SEIC", "SNH", "ST", "SCI", "SERV", "TRGP", 
            "TCO", "TCF", "AMTD", "TDY", "TDS", "TPX", "TDC", "TER", "TEX", "TSRO", "TSLA", "TCBI", 
            "TFSL", "CC", "WEN", "THO", "TKR", "TOL", "TMK", "TTC", "RIG", "TRU", "THS", "TRCO", 
            "TRMB", "TRN", "TRIP", "SNV", "DATA", "UBER", "UGI", "ULTI", "UMPQ", "USM", "X", "UTX", 
            "UTHR", "UNIT", "UNVR", "OLED", "URBN", "USFD", "VMI", "VVV", "VVC", "VEEV", "VER", "VRSK", 
            "VSM", "VIA", "TWLO", "TYL", "USG", "UBNT", "WBC", "WSO", "W", "WFT", "WBS", "WRI", "WBT", 
            "WCG", "WCC", "WST", "WAL", "WLK", "WEX", "WTM", "WLL", "JWA", "WSM", "WTFC", "WDAY", "WP", 
            "WPX", "WH", "VIAB", "VICI", "VIRT", "VC", "VST", "VOYA", "ZAYO", "ZEN", "ZG", "XPO", "YUMC",
            "SPOT", 'KDDIY', 'CHL', 'SEDG', 'SHAK', 'STMP', 'SUN', 'SYNH', 'TKC', 'TNDM', 'WUBA', 'XLRN', 
            'XPO', 'YETI', 'YY', 'AAXN', 'ACAD', 'ACIA', 'AMRN', 'ANGI', 'APPF', 'ARNA', 'ARWR', 'AYX', 
            'BL', 'BLDR', 'BZUN', 'CYBR', 'EQM', 'ERI', 'ETRN', 'EVBG', 'FIVN', 'FOLD', 'GDS', 'GKOS', 
            'GLOB', 'GRUB', 'GWPH', 'HQY', 'HUBS', 'HZNP', 'ICPT', 'ICUI', 'IPHI', 'IRTC', 'JHG', 'JLL', 
            'LIVN', 'MIME', 'MOMO', 'MRCY', 'NEO', 'NEWR', 'NVCR', 'NVRO', 'NVTA', 'NXST', 'PCTY', 'PEN', 
            'PTCT', 'QTWO', 'RDFN', 'RGEN', 'RPD', 'RUN', 'SBSW', 'FL', 'ILMN',
            #Home healthcare providers
            'AMED', 'TDOC', 'LHCG', 'EHC', 'BKD',
            #Recent startups
            'O', 'DDOG', 'FSLY', 'PLL', 'LTRN', 'DYFN', 'VERI', 'CVNA', 'SDGR',
            'TXG', 'CRWD', 'PD', 'PINS', 'WORK', 'PDD', 'ZS', 'SPCE', 'GOLF',
            'CWH', 'COUP', 'MRAM', 'TWNK', 'LN', 'NH', 'RRR', 'SCWX', 'TRVG',
            'BABA', 'ROKU', 'SFIX', 'YOGA', 'YEXT', "WOW", "VODA", "SOGO",
            "SNAP", "SECO", "SNDR", "RBB", "ROVIO", "REMEDY", "RDFN", "QD", "KIDS",
            "NMRK", "NWGN", "MDB", "LAUR", "JELD", "ALTR", "ATUS", "AQ", "BAND",
            "APRN", "BXG", "BOKU", "BY", "GOOS", "CARG", "CARS", "CLDR", "FRII",
            "FNKO", "FOOD", "IR", "SQM", "AMRC", "AMKR", "MTEX", "BEDU", "CO", 
            "ITP", "CRUS", "VF", "SPX", "TREE", "PLUG", "LC", "ONVO", "XONE",
            "TWST", "MCRB", "SYRS", "IRDM", "IOVA", "VCYT", "NSTG", "MTLS", "CERS",
            "SSYS", "CGEN", "EDIT", "NTLA", "PRLB", "CRSP", 'EADSY', 
            "MRNA", 'PHAS', 'MGTA', 'XNCR', 'LAC', 'WIX', 'FIT', 'INO', 'DVAX',
            'NVAX', 'SRNE', 'ARCT', 'IBIO', 'WKHS', 'SHLL', 'FMCI', 'DKNG', 'VRM',
            'GNUS', 'OPES', 'IDEX', 'ZI', 'LCA', 'MELI', 'SE', 'BILI', 'LEVI']

  #ADD MCAP, MONEY/SHARE, DEBT/SHARE 

  #DUPLICATES: 
  stocks = ['MELI', 'SE', 'BILI']
  #stocks = ['DIS', 'AAPL', 'NVDA', 'AMD', 'MSFT', 'AMZN', 'CSCO', 'INTC', 'ETSY', 'ZNGA', 'KO', 'KR']
    
  # ETFS -> 'QQQ', 'SKYY', 'SPHD', 'VYM', 'VTI', 'VOO', 'SPY', 'VOOG', 
  # 'VOOV'

  df = pd.DataFrame({})

  for index, st in enumerate(stocks):
    print("\n*** At",st,":", index,"of",len(stocks),"***")
    #if index > 200:
    #  break
    try:
      yInfo = getCurrentFinancialInfo(st)
      #print("Financial: "+str(fInfo))
      msnInfo = getMSNMoneyFinancials(st,"analysis")

      if 'current_price' in msnInfo:
        yInfo['current_price'] = msnInfo['current_price']
      
      if 'post_price' in msnInfo:
        yInfo['post_price'] = msnInfo['post_price']

      if 'high_5y_pe' in msnInfo: 
        yInfo['high_5y_pe'] = msnInfo['high_5y_pe']
      
      if 'low_5y_pe' in msnInfo:
        yInfo['low_5y_pe'] = msnInfo['low_5y_pe']

      #print("Values:"+str(yInfo))
      #print("")

      eps = yInfo['eps']
      growth_rate = 0
      try:
        if 'annual_growth' in yInfo and yInfo['annual_growth'] != None:
          growth_rate = float(yInfo['annual_growth'].replace("%",""))/100.0
          #print("Growth rate as number:"+str(growth_rate))
        else:
          print("Annual growth missing!")
      except (ValueError, TypeError):
        print("ERROR, cound not parse growth rate:<"+str(yInfo['annual_growth'])+">")
      
      dividend = 0.0
      if yInfo['forward_dividend_yield']:
        try:
          dividend = float(yInfo['forward_dividend_yield'].replace("%",""))/100.0
        except (ValueError, TypeError):
          dividend = 0.0
      
      #min_return = 0.15 # 15%
      #safety_margin = 0.5 # 50%
      #forward_pe = yInfo['forward_pe']
      #years = 10

      #buy_prices = []
      #fair_values = []

      #YAHOO
      #eps_future, stock_price_future, stock_fair_value, buy_stock_price = calcIntrinsicValue(eps, 
      #          growth_rate, dividend, min_return, safety_margin, forward_pe, years)
      
      #print("%s -> Curr: %s, In %i years -> eps: %.2f, stock_price: %.2f, Current -> Fair value: %.2f, buy price: %.2f" % 
      #(st, yInfo['current_price'], years, eps_future, stock_price_future, stock_fair_value, buy_stock_price))

      #buy_prices.append(buy_stock_price)
      #fair_values.append(stock_fair_value)

      #MSN MONEY
      #forward_pe = 0
      #if yInfo['high_5y_pe'] != None and yInfo['low_5y_pe'] != None:
      #  forward_pe = (yInfo['high_5y_pe'] + yInfo['low_5y_pe'])/2.

      #eps_future, stock_price_future, stock_fair_value, buy_stock_price = calcIntrinsicValue(eps, 
      #          growth_rate, dividend, min_return, safety_margin, forward_pe, years)
      
      #print("%s -> Curr: %s, In %i years -> eps: %.2f, stock_price: %.2f, Current -> Fair value: %.2f, buy price: %.2f" % 
      #(st, yInfo['current_price'], years, eps_future, stock_price_future, stock_fair_value, buy_stock_price))

      #buy_prices.append(buy_stock_price)
      #fair_values.append(stock_fair_value)

      yInfo['stock'] = st
      yInfo['growth_rate'] = growth_rate
      #yInfo['future_eps'] = eps_future
      #yInfo['future_price'] = stock_price_future
      #yInfo['fair_value_min'] = np.min(fair_values)
      #yInfo['fair_value_max'] = np.max(fair_values)
      #yInfo['buy_price_min'] = np.min(buy_prices)
      #yInfo['buy_price_max'] = np.max(buy_prices)
      yInfo['div_yield'] = dividend*100

      curr_price = None
      if 'current_price' in yInfo:
        curr_price = yInfo['current_price']
        if 'post_price' in yInfo:
          if yInfo['post_price'] != curr_price:
            curr_price = yInfo['post_price']

      yInfo['current_price'] = curr_price

      # Market Cap
      yInfo['MCap'] = None
      if 'market_cap' in yInfo and yInfo['market_cap'] != None:
        yInfo['MCap'] = compactNumber(yInfo['market_cap'])
      
      #Cash per share
      try:
        yInfo['cash_ps'] = round(yInfo['cash']/yInfo['n_shares'],2)
      except TypeError:
        print("cash_ps type error!")

      #Debt per share
      try:  
        yInfo['debt_ps'] = round(yInfo['debt']/yInfo['n_shares'],2)
      except TypeError:
        print("debt_ps type error!")
      
      #Net Cash per share
      try:
        yInfo['net_cash_ps'] = round((yInfo['cash'] - yInfo['debt'])/yInfo['n_shares'],2)
      except TypeError:
        print("net_cash_ps type error!")

      #histF = getHistoricFinancialInfo(st, 2016)
    except requests.exceptions.ReadTimeout:
      print("!!!!!!!!!! ERROR ReadTimeout adding empty: "+str(st))
      
      yInfo = {}
      yInfo['stock'] = st

    #add the current holdings
    if len(df_hld[df_hld.index==st])>0:
      yInfo['price'] = df_hld[df_hld.index==st]['price'].values[0]
      yInfo['number'] = df_hld[df_hld.index==st]['number'].values[0]
    else:
      yInfo['price'] = None
      yInfo['number'] = None

    #Save to DF
    df = df.append(yInfo, ignore_index=True)

    sel_cols = ['stock', 'MCap', 'current_price',
                '50_day_moving_avg', '200_day_moving_avg',
                'cash_ps', 'debt_ps', 'net_cash_ps',
                "peg_ratio", "price_sales", "price_book", "ev_rev",
                "q_revenue_growth", "q_earnings_growth",
                'growth_rate', 'eps', 'trailing_pe', 'forward_pe', 'high_5y_pe', 'low_5y_pe',
                'div_yield', 'price', 'number']

    print(df[-1:][sel_cols])

    dt_str = pstnow().strftime('%d_%m_%Y')
    filename_short = "intrinsic_values/tt_intrinsic_values_"+str(dt_str)+".csv" 
    #filename_full = "dividend_data/dividend_stock_"+str(dt_str)+".csv"
    #print("Filename:", filename)
    df[sel_cols].to_csv(filename_short, float_format='%.2f', index = None, header=True)
    #df.to_csv(filename_full, float_format='%.2f', index = None, header=True)

    wait_time = random.randint(1,5)
    print("\t\tWait: "+str(wait_time))
    time.sleep(wait_time)


  #print(dataset)
  
  #df = pd.DataFrame(dataset, 
  #columns=['stock','current_price','50_day_moving_avg', '200_day_moving_avg',
  #'buy_price_min','buy_price_max',
  #'fair_value_min','fair_value_max',
  #'growth_rate', 'eps', 'trailing_pe', 'forward_pe', 'high_5y_pe', 'low_5y_pe',
  #'div_yield'])

  #dt_str = pstnow().strftime('%d_%m_%Y')
  #filename = "intrinsic_values/intrinsic_values_"+str(dt_str)+".csv" 
  #print("Filename:", filename)
  #df.to_csv(filename, float_format='%.2f', index = None, header=True)



  #sPrice = getStockPrices("MSFT", "quote")
  #print("Stock prices: "+str(sPrice))


