''' This script initializes the input file of the simulator. 
Some preliminary data processing is done here.
'''
import sys
import csv
import numpy as np

''' Add power profile to each job
'''
try:
    with open('jobInfoPack.csv', 'r', encoding='utf-8') as csvInput:
        with open('jobInfoPack_ga.csv', 'w', encoding='utf-8') as csvOutput:
            writer = csv.writer(csvOutput, lineterminator='\n')
            reader = csv.reader(csvInput)
        
            all = []
            row = next(reader)
            row.append('Power')
            all.append(row)
            
            for row in reader:
                row.append(round(np.random.uniform(30, 50), 2))
                all.append(row)
            writer.writerows(all)
except:
    print("Unexpected error when pre-processing job information:", sys.exc_info()[0]) 
    exit()
    
''' List of problem: 2016.3.27 2:00:00 no price
                     2017.3.26 2:00:00 no price
'''