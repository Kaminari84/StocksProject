from flask import Flask, request, make_response, render_template, current_app, g
import json
import os
import numpy as np
from random import random
from scipy.special import softmax
import pandas as pd
from datetime import datetime
from sklearn.svm import SVR
from sklearn.metrics import mean_squared_error

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['EXPLAIN_TEMPLATE_LOADING'] = True
env = app.jinja_env
env.add_extension("jinja2.ext.loopcontrols") #Loop extension to enable {% break %}

app.app_context().push() #server context - enables storage of variables between sessions


#http://kronosapiens.github.io/blog/2014/08/14/understanding-contexts-in-flask.html
#https://github.com/Kaminari84/GCloud_work_reflection_bot/blob/master/dataMgr.py
#https://botsociety.io/blog/2019/03/botsociety-dialogflow/
#https://medium.com/@jonathan_hui/rl-model-based-reinforcement-learning-3c2b6f0aa323
#https://towardsdatascience.com/model-based-reinforcement-learning-cb9e41ff1f0d

def setup_app(app):
    print("Loading the server, first init global vars...")
    #DataMgr.load_team_auths()
    #logging.info('Creating all database tables...')
    #db.create_all()
    #logging.info('Done!')

    #print("ENVIRON TEST:", os.environ['TEST_VAR'])

    with app.app_context():
        # within this block, current_app points to app.
        print("App name:",current_app.name)

    print("Start the actual server...")

setup_app(app)

# Server paths
@app.route('/')
def hello_world():
    return 'Hello, World!'
                    
@app.route('/plot_stock')
def appl_test():
    r = { 'history':{ 
        '2019-07-24': {'close': '208.67', 
                'high': '209.15', 
                'low': '207.17', 
                'open': '207.67', 
                'volume': '14991567'}, 
        '2019-07-25': {'close': '207.02', 
                'high': '209.24', 
                'low': '206.73', 
                'open': '208.89', 
                'volume': '13909562'}, 
        '2019-07-26': {'close': '207.74', 
                'high': '209.73', 
                'low': '207.14', 
                'open': '207.48',
                'volume': '17618874'} 
        }, 
    'name': 'AAPL'}

    #Load JSON
    f = open('static/AAPL.json', 'r')
    r = json.load(f)
    f.close()

    n = 0
    values = []
    for key in sorted(r['history'].keys(), reverse=True):
        val = r['history'][key]
        #print("Key:",key," ,Val:",val)
        values.append( { 'datetime': key, 'close': val['close'] } )
        n += 1
        if n>500:
            break

    return render_template('plot_stock.html',
        stock_prices = values
    )

@app.route('/plot_stock_c3')
def plot_stock_c3():
    r = { 'history':{ 
        '2019-07-24': {'close': '208.67', 
                'high': '209.15', 
                'low': '207.17', 
                'open': '207.67', 
                'volume': '14991567'}, 
        '2019-07-25': {'close': '207.02', 
                'high': '209.24', 
                'low': '206.73', 
                'open': '208.89', 
                'volume': '13909562'}, 
        '2019-07-26': {'close': '207.74', 
                'high': '209.73', 
                'low': '207.14', 
                'open': '207.48',
                'volume': '17618874'} 
        }, 
    'name': 'AAPL'}

    #Load JSON
    f = open('static/AAPL.json', 'r')
    r = json.load(f)
    f.close()

    n = 0
    values = []
    for key in sorted(r['history'].keys(), reverse=True):
        val = r['history'][key]
        #print("Key:",key," ,Val:",val)
        values.append( { 'datetime': key, 'close': val['close'] } )
        n += 1
        if n>500:
            break

    return render_template('plot_stock_c3.html',
        stock_prices = values
    )

@app.route('/invest_random')
def invest_random():
    investP = 0.01
    funds = 1000
    stocks = 0
    moves = []

    #Load JSON
    f = open('static/AAPL.json', 'r')
    r = json.load(f)
    f.close()

    n = 0
    values = []
    for key in sorted(r['history'].keys(), reverse=True):
        val = r['history'][key]
        #print("Key:",key," ,Val:",val)
        values.insert(0, { 'datetime': key, 'close': val['close'] } )
        n += 1
        if n>500:
            break

    total_value = 0
    for entry in values:
        #print("Checking entry:", entry)
        #enough money to buy?
        if (funds > float(entry['close'])):
            #decide if to buy
            if (random() <= investP):
                print("Buying at "+str(entry['datetime'])+", price: "+str(entry['close']))
                stocks += 1
                funds -= float(entry['close'])
                moves.append({'datetime':entry['datetime'], 'type': 'buy', 'price':entry['close'], 'stocks':stocks, 'funds':funds})
        
        #can sell? do we have stocks
        if (stocks>0):
            #decide if to sell
            if (random() <= investP):
                print("Selling at "+str(entry['datetime'])+", price: "+str(entry['close']))
                stocks -= 1
                funds += float(entry['close'])
                moves.append({'datetime':entry['datetime'], 'type': 'sell', 'price':entry['close'], 'stocks':stocks, 'funds':funds})
               
        total_value = funds + stocks*float(entry['close'])

    print("Total value: "+str(total_value))
    #Return predictions
    json_resp = json.dumps({'status': 'OK', 'message':'', 'moves':moves, 'total_value': total_value})
    
    return make_response(json_resp, 200, {"content_type":"application/json"})


@app.route('/getStockPredictions')
def get_stock_predictions():
    stock_ticket = request.args.get('stock_ticket')
    data_point = request.args.get('data_point')

    print("Stock ticket:",str(stock_ticket))
    print("Data point:", str(data_point))

    point_date = datetime.strptime(data_point, "%a %b %d %Y")

    print("Parsed date:", str(point_date.strftime("%d/%m/%y")))

    #Temp solution - replace with persistent storage
    f = open('static/AAPL.json', 'r')
    r = json.load(f)
    f.close()

    n = 0
    entries = {'datetime': [], 'close': []}
    for key in sorted(r['history'].keys(), reverse=True):
        val = r['history'][key]
        #print("Key:",key," ,Val:",val)
        entries['datetime'].append( key )
        entries['close'].append( float(val['close']) )
        n += 1
        if n>500:
            break

    df = pd.DataFrame(entries, columns=['datetime','close'])
    df['datetime'] = pd.to_datetime(df['datetime'])
    df.sort_values(by=['datetime'], inplace=True, ascending=True)
    #print(df.columns)
    print(df.shape)
    #print(df.head(10))

    # Mask - only select data points from the past from this point
    mask = (df['datetime'] < data_point)
    print(df.loc[mask].shape)
    print(df.loc[mask].head(10))

    #create the training data
    n_features = 3
    features = []
    prices = []

    feature_row = []
    print("Iterating through past data...")
    for index, row in df.loc[mask].iterrows():
        print("Index:", index, ", Date:", row['datetime'], ", Close:", row['close'])
        # If enough features in history set this price as the price to predict
        if len(feature_row) >= n_features:
            prices.append(row['close'])
            features.append(feature_row)
        
        # Shift forward by one data point
        feature_row = feature_row.copy()
        feature_row.append(row['close'])
        if len(feature_row) > n_features:
            feature_row.pop(0)

    print("Features:", features)
    print("Prices:", prices)
    
    features = np.reshape(features, (len(features), n_features))
    #print(features[:,0:n_features])
   
    #Initialize different models
    svr_lin = SVR(kernel='linear', C=1e3)
    svr_poly = SVR(kernel='poly', C=1e3, degree = 2) #, gamma='scale')
    svr_rbf = SVR(kernel='rbf', C=1e3, gamma='auto')

    #Train models
    svr_lin.fit(features[:,0:n_features], prices)
    svr_poly.fit(features[:,0:n_features], prices)
    svr_rbf.fit(features[:,0:n_features], prices)

    #Predict
    predict_lin = svr_lin.predict(features[:,0:n_features])
    predict_poly = svr_poly.predict(features[:,0:n_features])
    predict_rbf = svr_rbf.predict(features[:,0:n_features])

    #Evaluate
    print("Predicted prices - linear:",predict_lin[-5:])
    print("Predicted prices - RBF:",predict_rbf[-5:])
    print("MSE for linear - training:", mean_squared_error(prices, predict_lin))
    print("MSE for poly - training:", mean_squared_error(prices, predict_poly))
    print("MSE for RBF - training:", mean_squared_error(prices, predict_rbf))

    print("Test MSE low:",mean_squared_error([122.2, 134.5, 100.2], [122.1, 134.4, 100.2]))
    print("Test MSE high:",mean_squared_error([122.2, 134.5, 100.2], [112.1, 138.8, 105.9]))

    #Recursive prediction for k days ahead
    gen_features = features[-1,0:n_features].tolist()
    predictions = []
    print("Gen features, start:", gen_features)
    for day_i in range(30):
        #print("Gen features:", gen_features[-n_features:])
        form_features = np.reshape([gen_features[-n_features:]], (1, n_features))
        print("Iter ", day_i,", form features:", form_features[0])
        predict_rbf = svr_rbf.predict(form_features)
        pred = predict_rbf[0] #round(,2)
        gen_features.append(pred)
        predictions.append(pred)

    #Return predictions
    json_resp = json.dumps({'status': 'OK', 'message':'', 'predictions':predictions})
    
    return make_response(json_resp, 200, {"content_type":"application/json"})