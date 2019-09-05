import re
import os, sys
import statistics

curdir = os.path.abspath(sys.path[0])
os.chdir(curdir)

def compare_files(file_self, file_opt):
    with open(file_self) as f:
        read_data = f.read()
        
    own_data = re.findall(r"\d+", read_data)
    own_data = [int(t) for t in own_data]
    
    with open(file_opt) as f:
        read_data = f.read()
        
    opt_data = re.findall(r"\d+", read_data)
    opt_data = [int(t) for t in opt_data]
    
    count_opt = 0
    diff = []
    
    for i in range(len(own_data)):
        if own_data[i] == opt_data[i]:
            count_opt += 1
        if own_data[i] >= opt_data[i]:
            percent_dev = (own_data[i] - opt_data[i])/opt_data[i]
            diff.append(percent_dev)
        else:
            print('Check result')
    print('Number of values equal:', count_opt)
    print('Mean difference between values:', statistics.mean(diff))
    print("Standard deviation between values", statistics.stdev(diff))
    

compare_files('wtself40.txt', 'wtopt40.txt')
            