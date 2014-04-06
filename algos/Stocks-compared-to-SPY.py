# Put any initialization logic here.  The context object will be passed to
# the other methods in your algorithm.
global init
init = []
def initialize(context):
    # set_universe(universe.DollarVolumeUniverse(floor_percentile=98.0, ceiling_percentile=100.0))
    stock_name = ["SPY", "INTC", "AAPL", "NFLX", "ARMH", "QCOM"]  # initialize all stocks that you want tracked here. 
    # The first one should always be SPY as we track against it
    stocks = [sid(8554), sid(3951), sid(24), sid(23709), sid(18522), sid(6295)]
    context.other_sids = stocks  # add some specific securities    
    context.first_run = 1
    
def handle_data(context, data):
    if context.first_run is 1:
        context.first_run=0
        i=0
        for stock in context.other_sids:   
            init.append(data[stock].open_price)
            log.info(str(data[stock].open_price))
            i = i+1
        
        
    perf = []
    i=0

    for stock in context.other_sids:   
        performance=(data[stock].price - init[i])/init[i] 
        log.info("price = " + str(data[stock].price))
        log.info("init price = " + str(init[i]))
        log.info("perf = " + str(performance))
        perf.append(performance)
        i=i+1
    
    record(INTC=perf[1]/perf[0], AAPL=perf[2]/perf[0], NFLX=perf[3]/perf[0], ARM=perf[4]/perf[0], QCOM=perf[5]/perf[0])

