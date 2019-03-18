import sys
import pandas as pd
from datetime import datetime

# Construct energy two tariffs between two dates
def construct_energy_2tariffs(ran, daytarif=12, nighttarif=8, starttime=21, endtime=6):
    ind = pd.date_range(freq='H', start=ran[0], end=ran[1])
    prices = pd.DataFrame([daytarif] * len(ind), index=ind)
    night = (ind.weekday >= 5) | (ind.hour < endtime) | (ind.hour >= starttime) # saturday or sunday, after 21 and before 6
    prices[night] = nighttarif
    prices.columns = ['Euro']
    prices.index.name = 'Date'
    #prices = prices.loc[prices['Euro'].diff(1) != 0]
    return prices

if __name__ == "__main__":
    if (len(sys.argv) == 4):
        startdate = datetime.strptime(sys.argv[1], "%Y-%m-%d")
        enddate = datetime.strptime(sys.argv[2], "%Y-%m-%d")
        prices = construct_energy_2tariffs((startdate, enddate))
        prices.to_csv(sys.argv[3])
    else:
        print('Error')
