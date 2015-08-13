import datetime
import pandas as pd

def initialize(context):

    context.nasdaq_100 =     [sid(24),    sid(114),   sid(122),   sid(630),   sid(67),  \
                          sid(20680), sid(328),   sid(14328), sid(368),   sid(16841), \
                          sid(9883),  sid(337),   sid(38650), sid(739),   sid(27533), \
                          sid(3806),  sid(18529), sid(1209),  sid(1406),  sid(1419),  \
                          sid(15101), sid(17632), sid(39095), sid(1637),  sid(1900),  \
                          sid(32301), sid(18870), sid(14014), sid(25317), sid(36930), \
                          sid(12652), sid(26111), sid(24819), sid(24482), sid(2618),  \
                          sid(2663),  sid(27543), sid(1787) , sid(2696),  sid(42950), \
                          sid(20208), sid(2853),  sid(8816),  sid(12213), sid(3212),  \
                          sid(9736),  sid(23906), sid(26578), sid(22316), sid(13862), \
                          sid(3951),  sid(8655),  sid(25339), sid(4246),  sid(43405), \
                          sid(27357), sid(32046), sid(4485),  sid(43919), sid(4668),  \
                          sid(8677),  sid(22802), sid(3450),  sid(5061),  sid(5121),  \
                          sid(5149),  sid(5166),  sid(23709), sid(13905), sid(19926), \
                          sid(19725), sid(8857),  sid(5767),  sid(5787),  sid(19917), \
                          sid(6295),  sid(6413),  sid(6546),  sid(20281), sid(6683),  \
                          sid(26169), sid(6872),  sid(11901), sid(13940), sid(7061),  \
                          sid(15581), sid(24518), sid(7272),  sid(39840), sid(7671),  \
                          sid(27872), sid(8017),  sid(38817), sid(8045),  sid(8132),  \
                          sid(8158),  sid(24124), sid(8344),  sid(8352),  sid(14848)]

    context.rebalance_year = None
    context.rebalance_month = None

def get_returns(datapanel):
    
  # get the dataframe of prices 
  
    prices = history(20,'1d','price')
    returns = prices.iloc[[0,-1]].pct_change()
  
  # return a dataframe with one row showing the averages for each stock.
    return returns.iloc[-1]

def handle_data(context, data):
    
    #Get the current exchange time in EST
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern') 
    today = get_datetime().date()
    if context.rebalance_year == None:
        context.rebalance_year = today.year
        context.rebalance_month = today.month
        
        
    if today.year > context.rebalance_year:
        context.rebalance_month = -1
        context.rebalance_year = today.year
        
    if today.month > context.rebalance_month:
        if exchange_time.hour == 9 and exchange_time.minute == 59:
            returns = get_returns(data)
            context.sids = data.keys()
                
            #sort stocks based on their returns so far this month: 
            returns_sorted = returns.copy()
            returns_sorted.sort()

            ranking = returns_sorted.keys()

            decile = round(len(context.sids)/10)
            top = set(ranking[-1*decile:])
            log.info(len(top))
            pct = 1/float(len(top))
            log.info(pct)
                

            for sid in context.sids:
                if sid not in top:
                    pos = context.portfolio.positions[sid]  
                    if pos.amount != 0:
                        order(sid, -1 * pos.amount)
                if sid in top:
                    order_target_percent(sid, pct)
                context.rebalance_month = today.month
                   
            log.info('rebalanced %s' % str(today))
        else:
            return
        
        

