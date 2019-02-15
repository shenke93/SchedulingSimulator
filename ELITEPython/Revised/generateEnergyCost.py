''' This file is used to generate energy prices according to the energy policy,
    in a fixed date range.
'''

from datetime import datetime
from dateutil import rrule
import csv


# Policy 1: TOU(Time of Use), picked from Belpex, the csv file is downloaded and provided outside.
# Policy 2: Peak and off-peak pricing

# Step1: Provide a date range as the input: Start_time and End_time

def get_price(time, peak_start, peak_end):
    h = time.hour
    if peak_start <= h < peak_end:
        return 35
    else:
        return 15
    

start_time = datetime(2016, 11, 3, 6, 0)
end_time = datetime(2016, 11, 8, 0, 0)
peak_start = 9
peak_end = 20

with open('electricity_price.csv', 'w', newline='\n') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['Date', 'Euro'])
    for i in rrule.rrule(rrule.HOURLY, dtstart=start_time, until=end_time):
        price = get_price(i, peak_start, peak_end)
        writer.writerow([i, price])
