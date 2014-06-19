import pandas as pd
import numpy as np
import copy
import QSTK.qstkutil.qsdateutil as du
import QSTK.qstkutil.tsutil as tsu
import datetime as dt
import math
import QSTK.qstkutil.DataAccess as da
from bolingerplot import bbplot
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def generate_orders(ls_symbols, d_data,ldt_timestamps,filename):
    ''' Generate orders based on technical indicators
    such as Bollinger feature'''
    
    df_close = d_data['close']

    # Creating an empty dataframe for orders
    orders = pd.DataFrame(columns=['Year','Month','Day','Symbol','Order','Share'])

    # Creating empty dataframes for detecting event, (bollinger) indicator values, rolling mean, upper and lower bounds
    df_events = copy.deepcopy(df_close)
    df_events = df_events * np.NAN
    bb_value = df_events*np.NAN
    upper = df_events*np.NAN
    lower = df_events*np.NAN
    means = df_events*np.NAN
    
    for s_sym in ls_symbols:
        means[s_sym] = pd.rolling_mean(df_close[s_sym],20)
        std_sym = pd.rolling_std(df_close[s_sym],20)
        upper[s_sym] = means[s_sym] + std_sym
        lower[s_sym] = means[s_sym] - std_sym
        bb_value[s_sym] = (df_close[s_sym]-means[s_sym])/std_sym
    
    print "take one stock and look at its price fluctuation and Bollinger value along time"    
    symbol = raw_input('Which stock to look at (e.g., \'MSFT\', \'AAPL\'): ')
    bbplot(df_close,ldt_timestamps,means,upper,lower,symbol,bb_value)
    
    print
    print "-"*60
    print "Generating order sheet based on Bollinger Band"
    print "-"*60
    print 
     
    for s_sym in ls_symbols:
        for i in range(1, len(ldt_timestamps)):
            bb_today = bb_value[s_sym].ix[ldt_timestamps[i]]
            bb_yesterday = bb_value[s_sym].ix[ldt_timestamps[i-1]]
            bb_markettoday = bb_value['SPY'].ix[ldt_timestamps[i]]
            if bb_yesterday >= -2.0 and bb_today < -2.0 and bb_markettoday >= 1.1:
                newbuy = [ldt_timestamps[i].year,ldt_timestamps[i].month,ldt_timestamps[i].day,s_sym,'Buy',100]
                newbuy = pd.Series(dict(zip(orders.columns,newbuy)))
                orders=orders.append(newbuy,ignore_index=True)
                try:
                    newsell = [ldt_timestamps[i+5].year,ldt_timestamps[i+5].month,ldt_timestamps[i+5].day,s_sym,'Sell',100]
                except IndexError:
                    newsell = [ldt_timestamps[-1].year,ldt_timestamps[-1].month,ldt_timestamps[-1].day,s_sym,'Sell',100]
                newsell = pd.Series(dict(zip(orders.columns,newsell)))
                orders=orders.append(newsell,ignore_index=True)
    orders=orders.sort(columns=['Year','Month','Day'],ascending=True)
    orders.to_csv(filename,sep=',',index=False,header=False)
                
def totalvalue(cash_ini,orderform,valueform):
    
    trades = pd.read_csv(orderform,header=None,sep=',')
    trades = trades.dropna(axis = 1, how='all')
    trades.columns = ['Year','Month','Day','Symbol','Order','Share']
    dateall = []
    for i in np.arange(len(trades.Year)):
        dateall.append(dt.datetime(trades['Year'][i],trades['Month'][i],trades['Day'][i],16))
    dateall = pd.to_datetime(dateall)
    trades=trades.drop(['Year','Month','Day'],axis=1)
    trades['Date']=dateall
    trades.set_index('Date',inplace=True)
    
    ls_symbols = []
    for symbol in trades.Symbol:
        if symbol not in ls_symbols:
            ls_symbols.append(symbol)
            
    startdate = dateall[0]
    enddate = dateall[-1]
    dt_timeofday = dt.timedelta(hours=16)
    ldt_timestamps = du.getNYSEdays(startdate,enddate+dt_timeofday,dt_timeofday)
    ls_keys = 'close'
    c_dataobj = da.DataAccess('Yahoo')
    price = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    orders = price*np.NaN
    orders = orders.fillna(0)
    for i in np.arange(len(trades.index)):
        ind = trades.index[i]
        if trades.ix[i,'Order']=='Buy':
            orders.loc[ind,trades.ix[i,'Symbol']]+=trades.ix[i,'Share']
        else:
            orders.loc[ind,trades.ix[i,'Symbol']]+=-trades.ix[i,'Share']
    #    keys = ['price','orders']
    #    trading_table = pd.concat([ldf_data,orders],keys=keys,axis=1)
    cash = np.zeros(np.size(price[ls_symbols[0]]),dtype=np.float)
    cash[0] = cash_ini
    # updating the cash value
    for i in np.arange(len(orders.index)):
        if i == 0: 
            cash[i] = cash[i] - pd.Series.sum(price.ix[i,:]*orders.ix[i,:])
        else:
            cash[i] = cash[i-1] - pd.Series.sum(price.ix[i,:]*orders.ix[i,:])
    # updating ownership
    ownership = orders*np.NaN
    for i in np.arange(len(orders.index)):
        ownership.ix[i,:]=orders.ix[:i+1,:].sum(axis=0) 
        
    # updating total portofolio value
    value = np.zeros_like(cash)
    for i in np.arange(len(ownership.index)):
        value[i] = pd.Series.sum(price.ix[i,:]*ownership.ix[i,:]) 
    keys = ['price','orders','ownership']
    trading_table = pd.concat([price,orders,ownership],keys = keys, axis=1)
    trading_table[('value','CASH')]=cash
    trading_table[('value','STOCK')]=value
    total = np.zeros_like(cash)
    total = cash + value
    trading_table[('value','TOTAL')]=total
    trading_table[('value','TOTAL')].to_csv(valueform)

def comparemarket(valueform):
    daily_value = pd.read_csv(valueform,header=None,sep=',')
    startdate = dt.datetime.strptime(daily_value[0][0],'%Y-%m-%d %H:%M:%S')
    enddate = dt.datetime.strptime(daily_value.iloc[-1][0],'%Y-%m-%d %H:%M:%S')    
    dt_timeofday = dt.timedelta(hours=16)
    ldt_timestamps = du.getNYSEdays(startdate,enddate,dt_timeofday)       
    ls_keys = 'close'
    ls_symbols = ['$SPX']
    c_dataobj = da.DataAccess('Yahoo')
    bench = c_dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    port = np.zeros(np.size(bench))
    daily_value = daily_value.drop(0,1)
    for i in np.arange(len(bench.index)):
        port[i] = daily_value.ix[i]
    bench['ASSET']=port
    bench['Norm_SPX'] = bench['$SPX']/bench['$SPX'].ix[0]*bench['ASSET'].ix[0]
    fig = plt.figure(2)
    plt.clf()
    ax = fig.add_subplot(1,1,1)
    ax.plot(ldt_timestamps,bench['ASSET'],'r',label='ASSET')
    ax.plot(ldt_timestamps,bench['Norm_SPX'],'b',label='SPX')
    ax.legend(loc='best',prop={'size':10})
    ax.set_title('Portfolio vs SPX performance over time')
    ax.set_xlabel('Month\nYear')
    ax.set_ylabel('Value')
    ax.tick_params(labelbottom='off')
    ax.xaxis.set_minor_locator(mdates.MonthLocator(interval=1))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%m\n%Y'))
    plt.show()
    
    returns = bench.copy(deep=True)
    tsu.returnize0(returns['ASSET'])
    tsu.returnize0(returns['Norm_SPX'])
    # std of daily return
    std_asset = np.std(returns['ASSET'])
    std_spx = np.std(returns['Norm_SPX'])
    print '\n'
    print '_'*80
    print 'Comparison between the asset and the market performance'
    print '-'*80
    print '\n'
    print 'std of the asset: ', std_asset
    print 'std of SPX: ', std_spx
    print '\n'
    # average of daily return
    ave_asset = np.average(returns['ASSET'])
    ave_spx = np.average(returns['Norm_SPX'])
    print 'average daily return of the asset: ', ave_asset
    print 'average daily return of SPX: ', ave_spx
    print '\n'
    # total return/cumulative return
    cum_asset = np.cumprod(returns['ASSET']+1)[-1] 
    cum_spx = np.cumprod(returns['Norm_SPX']+1)[-1]
    print 'total return of the asset: ', cum_asset
    print 'total return of SPX: ', cum_spx
    print '\n'
    # sharp ratio
    sharp_asset = math.sqrt(252)*ave_asset/std_asset
    sharp_spx = math.sqrt(252)*ave_spx/std_spx
    print 'sharp ratio of the asset: ', sharp_asset
    print 'sharp ratio of SPX: ', sharp_spx
    print '\n'
                                                                 
def main():
    """ this is the main function """
    dt_start = raw_input('Please enter the starting date (in the format of mm/dd/yyyy): ')
    dt_start = dt.datetime.strptime(dt_start,"%m/%d/%Y")
    dt_end = raw_input('Please enter the end date (in the format of mm/dd/yyyy): ')
    dt_end = dt.datetime.strptime(dt_end,"%m/%d/%Y")
    
    ldt_timestamps = du.getNYSEdays(dt_start, dt_end, dt.timedelta(hours=16))

    dataobj = da.DataAccess('Yahoo')
    ls_symbols = dataobj.get_symbols_from_list('sp5002008')
    ls_symbols.append('SPY')

    ls_keys = ['close']
    ldf_data = dataobj.get_data(ldt_timestamps, ls_symbols, ls_keys)
    d_data = dict(zip(ls_keys, ldf_data))
    
    ## 'close' may not be the optimal, in future other features maybe used this session is to prepare for that
    for s_key in ls_keys:
        d_data[s_key] = d_data[s_key].fillna(method='ffill')
        d_data[s_key] = d_data[s_key].fillna(method='bfill')
        d_data[s_key] = d_data[s_key].fillna(1.0)
    
    # Time stamps for the event range
    ldt_timestamps = d_data['close'].index
    
    generate_orders(ls_symbols, d_data,ldt_timestamps,'neworders.csv')
    
    print "-"*40
    print "order sheet is saved as \'neworders.csv\'"
    print "-"*40
    print
    print "-"*80
    print "evaluating performance of the constructed asset against the market"
    totalvalue(100000,'neworders.csv','newvalues.csv')
    print
    print "total value of the constructed asset is saved in \'newvalue.csv\'"
    print "-"*80
    comparemarket('newvalues.csv')
    
if __name__ == '__main__':
    main()