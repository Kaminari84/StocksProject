
from os import path
import numpy as np
import datetime as dt
import pandas as pd

import json
import requests
import time
import pytz
from pytz import timezone
from pytz import common_timezones
from pytz import country_timezones

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

def scrapeHistoricFinancialInfo(stock, filename):
  #get historical financials (year)
  #Historic SEC filings - https://www.bamsec.com/companies/789019/microsoft-corp/chronological
  #Historic EPS - 10 years back - https://financials.morningstar.com/ratios/r.html?t=0P000003MH&culture=en&platform=sal
  #Historic dividends
  #Historic growth

  url_base_general = "https://www.morningstar.com/"
  url_add_pattern = "stocks/{s}/quote"
  url_final = url_base_general + url_add_pattern.replace("{s}",stock)

  print("-> Morningstar URL final:", url_final)

  financials = {}

  response = requests.get(url_final, timeout=20)
  if response.status_code == 200:
    #print("Rresp:",response.content.decode('utf-8'))
    #with open("morningstar_.html", 'w') as out:
    #  out.write(response.content.decode('utf-8'))

    page_content = BeautifulSoup(response.content, "lxml")
    #page_content.prettify()

    #current_price = page_content.find(class_="sal-component-key-stats-read-more")
    #print("SAL:"+str(current_price))
  
    #stocks-quote
    #class=sal-component-key-stats-read-more

    internal_stock_id = None

    js_elems = page_content.find_all("script")
    print("JS Elems Num:", len(js_elems))
    for js_elem in js_elems:
      js_text = js_elem.find(text=True)
      #print("JS elem text:", js_text)
      if js_text:
        if js_text.find('window.__NUXT__=') != -1:
            #print("js_text:"+str(js_text))
            js_text_str = str(js_text)
            search_idx = js_text_str.find('byId:')
            print("Found:"+str(search_idx))
            print("Substr:"+str(js_text_str[search_idx+7:search_idx+17]))

            internal_stock_id = js_text_str[search_idx+7:search_idx+17]

    #Get Financials
    if internal_stock_id != None:
      url_base_general = " https://financials.morningstar.com/"
      url_add_pattern = "finan/financials/getFinancePart.html?&callback=?&t={id}&region=usa&culture=en-US&version=SAL"
      url_final = url_base_general + url_add_pattern.replace("{id}",internal_stock_id)

      print("-> Internal URL final:", url_final)

      response = requests.get(url_final, timeout=20)
      if response.status_code == 200:
        #print("Rresp:",response.content.decode('utf-8'))
        html_text = response.content.decode('utf-8').replace('?({"componentData":"','').replace('"})','').replace('\\"','"').replace("\/","/")
        #with open("morningstar_financials.html", 'w') as out:
        #  out.write(html_text)

        page_content = BeautifulSoup(html_text, "lxml")
        #print(page_content)

        financials['stock'] = []
        financials['year'] = []

        text2label = { 
          'Revenue\xa0USD Mil': 'Revenue',
          'Revenue\xa0CNY Mil': 'Revenue',
          'Revenue\xa0JPY Mil': 'Revenue',
          'Gross Margin %': 'Gross Margin',
          'Operating Income\xa0USD Mil': 'Operating Income',
          'Operating Income\xa0CNY Mil': 'Operating Income',
          'Operating Income\xa0JPY Mil': 'Operating Income',
          "Operating Margin %": "Operating Margin",
          "Net Income\xa0USD Mil": "Net Income",
          "Net Income\xa0CNY Mil": "Net Income",
          "Net Income\xa0JPY Mil": "Net Income",
          "Earnings Per Share\xa0USD": "Earnings Per Share",
          "Earnings Per Share\xa0CNY": "Earnings Per Share",
          "Earnings Per Share\xa0JPY": "Earnings Per Share",
          "Dividends\xa0USD": "Dividends",
          "Dividends\xa0CNY": "Dividends",
          "Dividends\xa0JPY": "Dividends",
          "Payout Ratio % *": "Payout Ratio",
          "Shares\xa0Mil": "Shares",
          "Book Value Per Share *\xa0USD": "Book Value Per Share",
          "Book Value Per Share *\xa0CNY": "Book Value Per Share",
          "Book Value Per Share *\xa0JPY": "Book Value Per Share",
          "Operating Cash Flow\xa0USD Mil": "Operating Cash Flow",
          "Operating Cash Flow\xa0CNY Mil": "Operating Cash Flow",
          "Operating Cash Flow\xa0JPY Mil": "Operating Cash Flow",
          "Cap Spending\xa0USD Mil": "Cap Spending",
          "Cap Spending\xa0CNY Mil": "Cap Spending",
          "Cap Spending\xa0JPY Mil": "Cap Spending",
          "Free Cash Flow\xa0USD Mil": "Free Cash Flow",
          "Free Cash Flow\xa0CNY Mil": "Free Cash Flow",
          "Free Cash Flow\xa0JPY Mil": "Free Cash Flow",
          "Free Cash Flow Per Share *\xa0USD": "Free Cash Flow Per Share",
          "Free Cash Flow Per Share *\xa0CNY": "Free Cash Flow Per Share",
          "Free Cash Flow Per Share *\xa0JPY": "Free Cash Flow Per Share",
          "Working Capital\xa0USD Mil": "Working Capital",
          "Working Capital\xa0CNY Mil": "Working Capital",
          "Working Capital\xa0JPY Mil": "Working Capital"
        }

        #HEAD
        thead = page_content.find("thead").find("tr")
        #print("Thead:"+str(thead))
        col = 0
        for col_head_elem in thead.children:
          print("Col "+str(col)+":"+str(col_head_elem.text)) 
          col+=1

          if col_head_elem.text != '':
            financials['stock'].append(stock)
            year = col_head_elem.text[0:4]
            if year == "TTM":
              year = dt.datetime.now().year
            
            financials['year'].append(year)

        #BODY
        tbody = page_content.find("tbody")
        #EACH ROW IS STATS
        row = 0
        for row_elem in tbody.children:
          #print("Row "+str(row)+":"+str(row_elem))
          col = 0
          metric = []
          for col_elem in row_elem.children:
            #print("Col "+str(col)+":"+str(col_elem.text))
            col += 1
            val = col_elem.text

            if col_elem.text == '-':
              val = 0
            else:
              try:
                val = float(col_elem.text)
              except (ValueError, TypeError):
                pass

            metric.append(val)
          row += 1
          
          if metric[0] != '':
            print("Metric:"+str(metric[0]))

          if metric[0] in text2label:
            label = text2label[metric[0]]
  
            financials[label] = metric[1:]

          #if row>7:
          #  break

  #print("Financials:"+str(financials))
  master_df = pd.DataFrame()

  if path.exists(filename):
    master_df = pd.read_csv(filename, header=0)
    #print("---Loaded from FILE---")
    #print(master_df)

    #simulate missing data
    i = master_df[((master_df.year == '2019-09') & (master_df.stock == stock))].index
    master_df = master_df.drop(i)
    #print("---After drop df---")
    #print(master_df)

  add_df = pd.DataFrame(financials)
  #print("---Add df---")
  #print(add_df)

  new_master_df = pd.concat([master_df, add_df]).drop_duplicates(subset=['year','stock'])

  print("---New master df shape:", new_master_df.shape)
  print(new_master_df)

  if new_master_df.shape[0]>0:
    new_master_df.to_csv(filename, index = None, header=True)
    print(new_master_df.columns)

  return new_master_df

#Get the stock prices historical
def getStockPrices(stock, start, end):
  #url_base_general = "https://finance.yahoo.com/"
  #url_add_pattern = "{p}/{s}/history?period1=511056000&period2=1584921600&interval=1mo&filter=history&frequency=1mo"
  #url_final = url_base_general + url_add_pattern.replace("{s}",stock).replace("{p}",page)

  df = web.DataReader(stock, 'yahoo', start, end)

  return df

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


if __name__ == "__main__":
  ms_prefix = ['pinx', 'xnys', 'pinx', 'xnys',
              'xnas','xnys', 'xnas', 'xnas', 'xnys', 
              'xnys', 'xnas', 'xnas', 'xnas', 'xnas', 
              'xnas', 'xnas', 'xnas', 'xnys', 
              'xnas', 'xnys', 'xnys', 'xnys', 'xnys', 
              'xnas', 'xnas', 'xnys', 'xnas', 'xnas', 
              'xnys', 'xnys', 'xnys', 'xnys', 'xnas', 
              'xnys']
  
  stocks =    ['KDDIY', 'CHL', 'TCEHY', 'SQ',
              'ON', 'VMW', 'CSCO', 'AMZN','JNJ',
              'BLK', 'ADBE', 'SBUX', 'CSCO', 'AAPL', 
              'MSFT', 'NVDA', 'JPM', 'INTC', 
              'DIS', 'KO', 'KR', 'T', 'ADSK', 
              'GOOG', 'BA', 'FB', 'TXN', 'V', 
              'NOC', 'LMT', 'BAC', 'PEP', 'MMM', 'VZ']

  print(len(ms_prefix),"==",len(stocks))
  
  years = [2012,2013,2014,2015,2016,2017]

  '''
          "Dividends\xa0USD": "Dividends",
          "Payout Ratio % *": "Payout Ratio",
          "Shares\xa0Mil": "Shares",
          "Book Value Per Share *\xa0USD": "Book Value Per Share",
          "Operating Cash Flow\xa0USD Mil": "Operating Cash Flow",
          "Cap Spending\xa0USD Mil": "Cap Spending",
          "Free Cash Flow\xa0USD Mil": "Free Cash Flow",
          "Free Cash Flow Per Share *\xa0USD": "Free Cash Flow Per Share",
          "Working Capital\xa0USD Mil": "Working Capital"
  '''

  dataset = { "stock":[], 
              "year":[],
              "current_price": [],
              "fair_price": [],
              "ratio": [],
              "revenue": [],
              "gross_margin": [],
              "operating_income": [],
              "operating_margin": [],
              "net_income": [],
              "earnings_per_share": [],
              "dividends": [],
              "payout_ratio": [],
              "shares": [],
              "book_value_per_share": [],
              "price_1y": [],
              "price_2y": [],
              "price_3y": [],
              "ratio_1y": [],
              "ratio_2y": [],
              "ratio_3y": []
            }

for s_id in range(len(stocks)):
  stock = stocks[s_id]
  prfx = ms_prefix[s_id] 
  print("###STOCK:"+str(stock))

  start = dt.datetime(2010,1,1)
  end = dt.datetime(2020,3,27)

  df = getStockPrices(stock, start, end)
  #print(df.head())

  filename = 'historic_financials/financials_'+str(stock)+'.csv'
  if path.exists(filename):
    hFinance_df = pd.read_csv(filename, header=0)
  else:
    hFinance_df = scrapeHistoricFinancialInfo(prfx+"/"+stock, filename)

  #print("Historic financials:")
  #print(hFinance_df)
  #print(hFinance_df.info())
  hFinance_df['year'] = pd.to_numeric(hFinance_df['year'])

  for year in years:
    #print("Selected row:", hFinance_df.loc[hFinance_df['year'] == 2010]['Earnings Per Share'].values[0])
    print(" -> YEAR:"+str(year))

    # CALCULATE INTRINSIC VALUE IN THE PAST
    eps = float(hFinance_df.loc[hFinance_df['year'] == year]['Earnings Per Share'].values[0])

    growth_ratios = []
    #print("Max year:", hFinance_df['year'].max())
    for ny in range(year, hFinance_df['year'].max()):
      prev_eps = hFinance_df.loc[hFinance_df['year'] == ny]['Earnings Per Share'].values[0]
      curr_eps = hFinance_df.loc[hFinance_df['year'] == ny+1]['Earnings Per Share'].values[0]

      growth_ratios.append(float(curr_eps)/float(prev_eps) - 1)
      

    #print(np.mean(growth_ratios))

    #_avg_eps_growth = hFinance_df.loc[hFinance_df['year'] >= year]['Earnings Per Share'].mean()/eps-1
    #_num_years = hFinance_df.loc[hFinance_df['year'] >= year].shape[0]

    growth_rate = np.mean(growth_ratios) #_avg_eps_growth/_num_years

    hFinance_df['Dividends'] = pd.to_numeric(hFinance_df['Dividends'], errors='coerce')

    dividend = hFinance_df.loc[hFinance_df['year'] >= year]['Dividends'].mean()/100.
    min_return = 0.15 # 15%
    safety_margin = 0.5 # 50%

    avg_price = df.loc[df.index.year>= year]['Adj Close'].mean()
    avg_eps = hFinance_df.loc[hFinance_df['year'] >= year]['Earnings Per Share'].apply(pd.to_numeric).mean()
    
    forward_pe = avg_price/avg_eps
    forward_years = 10

    curr_price = df.loc[df.index.year == year]['Adj Close'].mean()

    print("\tEPS: %0.2f" % eps)
    print("\tGrowth rate: %0.2f" % growth_rate)
    print("\tDividend: %0.2f" % dividend)
    print("\tForward P/E: %0.2f" % forward_pe)

    eps_future, stock_price_future, stock_fair_value, buy_stock_price = calcIntrinsicValue(eps, 
          growth_rate, dividend, min_return, safety_margin, forward_pe, forward_years)

    print("%s -> Curr: %0.2f, In %i years -> eps: %.2f, stock_price: %.2f, Current -> Fair value: %.2f, buy price: %.2f" % 
    (stock, curr_price, forward_years, eps_future, stock_price_future, stock_fair_value, buy_stock_price))

    #Add row to the stock
    dataset['stock'].append(stock)
    dataset['year'].append(year)
    #Financials at the time
    revenue = hFinance_df.loc[hFinance_df['year'] == year]['Revenue'].values[0]
    try:
      revenue = revenue.replace(",","")
      if revenue == "-": revenue = None
    except:
      pass
    dataset['revenue'].append(revenue)

    gross_margin = hFinance_df.loc[hFinance_df['year'] == year]['Gross Margin'].values[0]
    dataset['gross_margin'].append(gross_margin)

    operating_income = hFinance_df.loc[hFinance_df['year'] == year]['Operating Income'].values[0]
    try:
      operating_income = operating_income.replace(",","")
      if operating_income == "-": operating_income = None
    except:
      pass
    dataset['operating_income'].append(operating_income)

    operating_margin = hFinance_df.loc[hFinance_df['year'] == year]['Operating Margin'].values[0]
    dataset['operating_margin'].append(operating_margin)
    #----Net Income 
    net_income = hFinance_df.loc[hFinance_df['year'] == year]['Net Income'].values[0]
    try:
      net_income = net_income.replace(",","")
      if net_income == "-": net_income = None
    except:
      pass
    dataset['net_income'].append(net_income)
    #-----Earnings Per Share
    earnings_per_share = hFinance_df.loc[hFinance_df['year'] == year]['Earnings Per Share'].values[0]
    dataset['earnings_per_share'].append(earnings_per_share)

    #-----Dividends
    dividends = hFinance_df.loc[hFinance_df['year'] == year]['Dividends'].values[0]
    dataset['dividends'].append(dividends)

    #-----Payout Ratio % 
    payout_ratio = hFinance_df.loc[hFinance_df['year'] == year]['Payout Ratio'].values[0]
    dataset['payout_ratio'].append(payout_ratio)

    #-----Shares\xa0Mil"
    shares = hFinance_df.loc[hFinance_df['year'] == year]['Shares'].values[0]
    try:
      shares = shares.replace(",","")
      if shares == "-": shares = None
    except:
      pass
    dataset['shares'].append(shares)

    #-----Book Value Per Share
    book_value_per_share = hFinance_df.loc[hFinance_df['year'] == year]['Book Value Per Share'].values[0]
    dataset['book_value_per_share'].append(book_value_per_share)

    
    #Calculated intrinsic value
    dataset['current_price'].append(curr_price)
    dataset['fair_price'].append(stock_fair_value)
    dataset['ratio'].append(curr_price/stock_fair_value)
    #Stock prices in future years
    dataset['price_1y'].append(df.loc[df.index.year == year+1]['Adj Close'].mean())
    dataset['price_2y'].append(df.loc[df.index.year == year+2]['Adj Close'].mean())
    dataset['price_3y'].append(df.loc[df.index.year == year+3]['Adj Close'].mean())
    dataset['ratio_1y'].append(df.loc[df.index.year == year+1]['Adj Close'].mean()/curr_price)
    dataset['ratio_2y'].append(df.loc[df.index.year == year+2]['Adj Close'].mean()/curr_price)
    dataset['ratio_3y'].append(df.loc[df.index.year == year+3]['Adj Close'].mean()/curr_price)

    time.sleep(1)
      
  hist_df = pd.DataFrame(dataset, columns=['stock','year',
  'revenue','gross_margin', 'operating_income', 'operating_margin', 'net_income', 'earnings_per_share',
  'dividends', 'payout_ratio', 'shares', 'book_value_per_share',
  'current_price','fair_price','ratio',
  'price_1y','price_2y','price_3y','ratio_1y', 'ratio_2y', 'ratio_3y'])

  hist_df.to_csv("historic_values.csv", float_format='%.2f', index = None, header=True)





