import numpy as np
import matplotlib.pyplot as plt
import csv

# DNA_SIZE
# POP_SIZE
# CROSS_RATE
# MUTATION_RATE
# N_GENERATIONS

''' Input: List of jobs (original schedule)
    Input file: jobInfo_ga.csv
    format: index(int), duration(float)
'''

''' Input: Energy price
    Input file: price_ga.csv
    format: date(date), price(float)
'''

def get_fitness(indiviaual):
    pass

if __name__ == '__main__':
    
    price_list = []
    schedule_origin = []
    
    with open('price_ga.csv', encoding='utf-8') as price_csv:
        reader = csv.DictReader(price_csv)
        for row in reader:
            price_list.append((row['Date'], row['Euro']))
    

    
    with open('jobInfo_ga.csv', encoding='utf-8') as jobInfo_csv:
        reader = csv.DictReader(jobInfo_csv)
        for row in reader:
            schedule_origin.append((row['ID'], row['Duration']))
     
#     print(price_list)        
#     print(schedule_origin)         