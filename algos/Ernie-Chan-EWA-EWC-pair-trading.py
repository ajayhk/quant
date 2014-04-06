import numpy as np
import pandas as pd
from collections import deque
from pytz import timezone

window_days = 28 # window length in minutes
window_minutes = window_days*390 # window length in minutes; each trading day has 390 minutes

def initialize(context):
    context.max_notional = 100000
    context.min_notional = -100000
    
    context.stocks = [sid(14516), sid(14517)]
    context.evec = [0.943, -0.822]
    context.unit_shares = 20
    context.tickers = [int(str(e).split(' ')[0].strip("Security(")) for e in context.stocks]    
    context.prices = pd.DataFrame({ k : pd.Series() for k in context.tickers } )
    context.previous_datetime = None
    context.new_day = None    
    set_commission(commission.PerShare(cost=0.00)) 
    
def handle_data(context, data):
    
    # skip tic if any orders are open or any stocks did not trade  
    for stock in context.stocks:  
        if bool(get_open_orders(stock)) or data[stock].datetime < get_datetime():  
            return
        
    current_datetime = get_datetime().astimezone(timezone('US/Eastern'))
    # detect new trading day
    if context.previous_datetime is None or current_datetime.day != context.previous_datetime.day:
        context.new_day = True
        context.previous_datetime = current_datetime       
        
    #log.info("len price: {lp}, window: {window}".format(lp = len(context.prices), window = window_days))
    if len(context.prices)<window_days and context.new_day:
        context.previous_datetime = get_datetime().astimezone(timezone('US/Eastern'))
        if intradingwindow_check(context):
            newRow = pd.DataFrame({k:float(data[s].price) for k,s in zip(context.tickers, context.stocks) },index=[0])
            context.prices = context.prices.append(newRow, ignore_index = True)
            context.new_day = False
    else: 
        if intradingwindow_check(context) and context.new_day:
            #context.new_day = False
            comb_price_past_window = np.zeros(len(context.prices))
            for ii,k in enumerate(context.tickers):
                comb_price_past_window += context.evec[ii]*context.prices[k]
            
            meanPrice = np.mean(comb_price_past_window); stdPrice = np.std(comb_price_past_window)
            comb_price = sum([e*data[s].price for e,s in zip(context.evec, context.stocks)])
            h = (comb_price - meanPrice)/stdPrice
            current_amount = []; cash_spent = [];
            for ii, stock in enumerate(context.stocks):
                current_position = context.portfolio.positions[stock].amount
                new_position = context.unit_shares * (-h) * context.evec[ii]
                current_amount.append(new_position)
                cash_spent.append((new_position - current_position)*data[stock].price)
                order(stock, new_position - current_position)
                context.new_day = False
                #log.info("ordered!")
            
            notionals = []
            for ii,stock in enumerate(context.stocks):
                #notionals.append((context.portfolio.positions[stock].amount*data[stock].price)/context.portfolio.starting_cash)
                notionals.append((context.portfolio.positions[stock].amount*data[stock].price)/context.portfolio.starting_cash)
            
            log.info("h = {h}, comb_price = {comb_price}, notionals = {notionals}, total = {tot}, price0 = {p0}, price1 = {p1}, cash = {cash}, amount = {amount}, new_cash = {nc}".\
                     format(h = h, comb_price = comb_price, notionals = notionals, \
                            tot = context.portfolio.positions_value + context.portfolio.cash, p0 = data[context.stocks[0]].price, \
                            p1 = data[context.stocks[1]].price, cash = context.portfolio.cash, amount = current_amount, \
                            nc = context.portfolio.cash - sum(cash_spent)))
            
            newRow = pd.DataFrame({k:float(data[s].price) for k,s in zip(context.tickers, context.stocks) },index=[0])
            context.prices = context.prices.append(newRow, ignore_index = True)
            context.prices = context.prices[1:len(context.prices)]    
            
            record(h = h, mPri = meanPrice)
            record(comb_price = comb_price)
            record(not0 = notionals[0], not1 = notionals[1])
        #if not context.new_day:
        #    log.info("time = {time}, cash = {cash}".format(cash = context.portfolio.cash, time = current_datetime))
        #record(price0 = data[context.stocks[0]].price*abs(context.evec[0]), price1 = data[context.stocks[1]].price*abs(context.evec[1]))
        #record(price0 = data[context.stocks[0]].price, price1 = data[context.stocks[1]].price)
    #record(port = context.portfolio.positions_value, cash = context.portfolio.cash)

def intradingwindow_check(context):
    # Converts all time-zones into US EST to avoid confusion
    loc_dt = get_datetime().astimezone(timezone('US/Eastern'))
    # if loc_dt.hour > 10 and loc_dt.hour < 15:
    if loc_dt.hour == 15 and loc_dt.minute > 0:
        return True
    else:
        return False

