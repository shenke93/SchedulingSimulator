import pickle

# Getting back objects
with open('data_IGA.pkl', 'rb') as f:
    iga_raw, iga_avg, iga_min, iga_max = pickle.load(f)

with open('data_CGA.pkl', 'rb') as f:
    cga_raw, cga_avg, cga_min, cga_max = pickle.load(f)
    
with open('data_RCA.pkl', 'rb') as f:
    rca_raw, rca_avg, rca_min, rca_max = pickle.load(f)
    
iga = iga_raw
cga = cga_raw
rca = rca_raw

# print(iga) # Not the ideal data for coverage analysis

def coverage(s1, s2):
    n = len(s2)
    t = 0
    flag = 0
    for i in s2:
        for j in s1:
            if j <= i: # if j dominates i
                flag = 1
                break
        if flag == 1: # pick i in the result
            t = t + 1
        flag = 0
    return t / n

t1 = [[] for _ in range(8) ]
# print(t)
for i in range(len(iga_raw)):
    if (i % 8 == 0):
        t1[0].append(iga_raw[i])
    if (i % 8 == 1):
        t1[1].append(iga_raw[i])
    if (i % 8 == 2):
        t1[2].append(iga_raw[i])
    if (i % 8 == 3):
        t1[3].append(iga_raw[i])
    if (i % 8 == 4):
        t1[4].append(iga_raw[i])
    if (i % 8 == 5):
        t1[5].append(iga_raw[i])
    if (i % 8 == 6):
        t1[6].append(iga_raw[i])
    if (i % 8 == 7):
        t1[7].append(iga_raw[i])


t2 = [[] for _ in range(8) ]
# print(t)
for i in range(len(cga_raw)):
    if (i % 8 == 0):
        t2[0].append(cga_raw[i])
    if (i % 8 == 1):
        t2[1].append(cga_raw[i])
    if (i % 8 == 2):
        t2[2].append(cga_raw[i])
    if (i % 8 == 3):
        t2[3].append(cga_raw[i])
    if (i % 8 == 4):
        t2[4].append(cga_raw[i])
    if (i % 8 == 5):
        t2[5].append(cga_raw[i])
    if (i % 8 == 6):
        t2[6].append(cga_raw[i])
    if (i % 8 == 7):
        t2[7].append(cga_raw[i])      
        
t3 = [[] for _ in range(8) ]
# print(t)
for i in range(len(rca_raw)):
    if (i % 8 == 0):
        t3[0].append(rca_raw[i])
    if (i % 8 == 1):
        t3[1].append(rca_raw[i])
    if (i % 8 == 2):
        t3[2].append(rca_raw[i])
    if (i % 8 == 3):
        t3[3].append(rca_raw[i])
    if (i % 8 == 4):
        t3[4].append(rca_raw[i])
    if (i % 8 == 5):
        t3[5].append(rca_raw[i])
    if (i % 8 == 6):
        t3[6].append(rca_raw[i])
    if (i % 8 == 7):
        t3[7].append(rca_raw[i])  

print("IGA over cga:")
for i in range(8):
#     print(t1[i])
#     print(t2[i])
    print(coverage(t1[i], t2[i]))

print("CGA over iga:")
for i in range(8):
    print(coverage(t2[i], t1[i]))
    
print("IGA over rca:")
for i in range(8):    
    print(coverage(t1[i], t3[i]))
 
print("RCA over iga")   
for i in range(8):    
    print(coverage(t3[i], t1[i]))
    
print("CGA over rca")   
for i in range(8):    
    print(coverage(t2[i], t3[i]))
    
print("RCA over cga")   
for i in range(8):    
    print(coverage(t3[i], t2[i]))   