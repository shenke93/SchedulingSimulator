import pickle

# Getting back objects
with open('y_ax_IGA.pkl', 'rb') as f:
    iga = pickle.load(f)
    
print("iga:", iga)

with open('y_ax_RCA.pkl', 'rb') as f:
    rca = pickle.load(f)

print("rca:", rca)    

with open('y_ax_CGA.pkl', 'rb') as f:
    cga = pickle.load(f)

print("cga:", cga)

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

print("IGA over cga:")
for i in range(8):
    print(coverage(iga[i*50:(i+1)*50], cga[i*50:(i+1)*50]))

print("CGA over iga:")
for i in range(8):
    print(coverage(cga[i*50:(i+1)*50], iga[i*50:(i+1)*50]))
    
print("IGA over rca:")
for i in range(8):    
    print(coverage(iga[i*50:(i+1)*50], rca[i*50:(i+1)*50]))
 
print("RCA over iga")   
for i in range(8):    
    print(coverage(rca[i*50:(i+1)*50], iga[i*50:(i+1)*50]))
    
print("CGA over rca")   
for i in range(8):    
    print(coverage(cga[i*50:(i+1)*50], rca[i*50:(i+1)*50]))
    
print("RCA over cga")   
for i in range(8):    
    print(coverage(rca[i*50:(i+1)*50], cga[i*50:(i+1)*50]))