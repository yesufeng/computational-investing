This is the final project from the "Computational Investing I" class.

The QSToolKit installation Guide is here:http://wiki.quantsoftware.org/index.php?title=QSToolKit_Installation_Guide.

The goal of this project is to build an automatic trading strategy and test its performance against the market. Concretely, S&P 500 stock data is extracted from Yahoo finance. Some events (technical indicator, here Bollinger value is used) derived from the stock¡¯s price fluctuation can be used as a trigger for an automatic trading action. For example, if the stock price is going down while the market is going up. It might be a good time to hold a long position of the stock and then short it five days later. And this automatic trading strategy is implemented and the performance of the constructed portfolio in terms of risk and average return can be tested against the market data.  

The trading.py contains three major functions: 1. automatically generate trades; 2. update total asset value and 3. compare asset performance against the market performance using the S&P 500 index.

1. generate_orders()
a trade will be triggered by the event suggested in class. To describe the event, first introduce the Bollinger value of that stock, which is the difference between the price of the stock that day and the 20 days rolling mean of its price divided by the std of the past 20 days. So an event is defined as whenever the Bollinger value of a stock drops below -2(was above -2 the previous day), at the same time, the Bollinger value of the market (indicated by the SPX in NYSE) is above 1.1. Then a trade is triggered, which buys in 100  shares of that stock and will sell it out 5 days later. This strategy is provided in class, tailored specifically for the period from 01/2008 to 12/2009. Data mining on different features/indicators to keep updating the strategy is the on-going project. 

2. totalvalue()
The 2nd function is to update the total asset value along with this trading strategy after the market closes on every trading day. Initially input 100,000$ cash I want to update the total asset value, which is cash plus stock value in real time and save it into another csv form. 

3. comparemarket()
The 3rd function is to compare the performance of this constructed portfolio against the market's (S&P 500) performance, which is represented by the "SPX" index in Yahoo finance.

