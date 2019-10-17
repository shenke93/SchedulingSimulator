import re
import os, sys
import statistics

CHOICE = [40, 50, 100]
NUM = CHOICE[0]
FILE_SELF = f'wtself{NUM}.txt'
if NUM <= 50:
    FILE_OPT = f'wtopt{NUM}.txt'
else:
    FILE_OPT = f'wtbest{NUM}b.txt'

curdir = os.path.abspath(sys.path[0])
os.chdir(curdir)

def read_ints(file):
    read_data = file.read()
    data = re.findall(r"\d+", read_data)
    data = [int(t) for t in data]
    return data

def compare_files(file_self, file_opt):
    with open(file_self) as f:
        own_data = read_ints(f)
    
    with open(file_opt) as f:
        opt_data = read_ints(f)
    
    count_opt = 0
    diff = []
    diff_perc = []
    
    for i in range(len(own_data)):
        if own_data[i] == opt_data[i]:
            count_opt += 1
        if own_data[i] < opt_data[i]:
            print('Check result')
        dev = own_data[i] - opt_data[i]
        if opt_data[i] != 0:
            dev_perc = dev / opt_data[i]
        else:
            pass
        diff.append(dev)
        diff_perc.append(dev_perc)
        # print(dev)
        # print(dev_perc)
        # input()

    print(f'Comparing {FILE_SELF} and {FILE_OPT}')
    print('Number of values equal:', count_opt)
    mean = statistics.mean(diff)
    print('Mean difference between values:', mean)
    stdev = statistics.stdev(diff)
    print("Standard deviation between values:", stdev)
    maxdev = max(diff)
    print("Maximal deviation between values:", maxdev)
    mean_perc = statistics.mean(diff_perc)
    print(f'Mean percentual deviation between values: {mean_perc:.2%}')
    max_perc = max(diff_perc)
    print(f'Max percentual deviation between values: {max_perc:.2%}')

compare_files(FILE_SELF, FILE_OPT)
            