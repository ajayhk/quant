
def initialize(context):
    context.max = 10000               # The amount you are willing to invest
    context.buy_and_hold_number = 0   # Number of stocks that you can buy for B&H
    context.run_once = 0              # Any code that should be run once only  
    context.stock_traded = sid(24)    # AAPL to show the increase

def handle_data(context, data):

    if context.run_once == 0:
        # calculate number of stocks to buy
        context.buy_and_hold_number = context.max/data[context.stock_traded].price
        context.run_once = 1
    
    buy_and_hold_value = 0
    # This is the graph of what would happen if we had just bought and kept
    buy_and_hold_value = context.buy_and_hold_number * data[context.stock_traded].price
    record(BuyAndHold=buy_and_hold_value)

    # This is the graph of our current portfolio
    record(PortfolioValue=context.portfolio.positions_value + int(context.portfolio.cash))

    ##### Your algo here #####
    if (data[context.stock_traded].price < data[context.stock_traded].mavg(20)) and \
    context.portfolio.positions[context.stock_traded].amount == 0 : 
        order(context.stock_traded, 20)
    if (data[context.stock_traded].price > data[context.stock_traded].mavg(20)) and \
    context.portfolio.positions[context.stock_traded].amount != 0 : 
        order(context.stock_traded, -20)
    ##### End of algo #####

