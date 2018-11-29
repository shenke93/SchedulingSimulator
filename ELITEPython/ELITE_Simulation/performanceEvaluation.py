import pickle
import numpy as np
import matplotlib
import matplotlib.pyplot as plt

# Getting back objects
with open('data_IGA.pkl', 'rb') as f:
    iga_raw, iga_avg, iga_min, iga_max = pickle.load(f)

with open('data_CGA.pkl', 'rb') as f:
    cga_raw, cga_avg, cga_min, cga_max = pickle.load(f)
    
with open('data_RCA.pkl', 'rb') as f:
    rca_raw, rca_avg, rca_min, rca_max = pickle.load(f)
    
# print(iga_min)
# print(cga_min)
# print(rca_min)
# exit()
    
# print(iga_raw)
# print(len(iga_raw))
t = [[] for _ in range(8) ]
# print(t)
for i in range(len(iga_raw)):
    if (i % 8 == 0):
        t[0].append(iga_raw[i])
    if (i % 8 == 1):
        t[1].append(iga_raw[i])
    if (i % 8 == 2):
        t[2].append(iga_raw[i])
    if (i % 8 == 3):
        t[3].append(iga_raw[i])
    if (i % 8 == 4):
        t[4].append(iga_raw[i])
    if (i % 8 == 5):
        t[5].append(iga_raw[i])
    if (i % 8 == 6):
        t[6].append(iga_raw[i])
    if (i % 8 == 7):
        t[7].append(iga_raw[i])

# print(t[7].count(np.min(t[7])))

# exit()

iga_std = np.std(t, axis=1, ddof=1)
# print(np.mean(t, axis=1))
# print(iga_avg)
# print(np.max(t, axis=1))
# print(iga_max)

t = [[] for _ in range(8) ]
# print(t)
for i in range(len(cga_raw)):
    if (i % 8 == 0):
        t[0].append(cga_raw[i])
    if (i % 8 == 1):
        t[1].append(cga_raw[i])
    if (i % 8 == 2):
        t[2].append(cga_raw[i])
    if (i % 8 == 3):
        t[3].append(cga_raw[i])
    if (i % 8 == 4):
        t[4].append(cga_raw[i])
    if (i % 8 == 5):
        t[5].append(cga_raw[i])
    if (i % 8 == 6):
        t[6].append(cga_raw[i])
    if (i % 8 == 7):
        t[7].append(cga_raw[i])

# print(t[7].count(np.max(t[7])))
# 
# exit()

cga_std = np.std(t, axis=1, ddof=1)

t = [[] for _ in range(8) ]
# print(t)
for i in range(len(rca_raw)):
    if (i % 8 == 0):
        t[0].append(rca_raw[i])
    if (i % 8 == 1):
        t[1].append(rca_raw[i])
    if (i % 8 == 2):
        t[2].append(rca_raw[i])
    if (i % 8 == 3):
        t[3].append(rca_raw[i])
    if (i % 8 == 4):
        t[4].append(rca_raw[i])
    if (i % 8 == 5):
        t[5].append(rca_raw[i])
    if (i % 8 == 6):
        t[6].append(rca_raw[i])
    if (i % 8 == 7):
        t[7].append(rca_raw[i])
        
print(t[7].count(np.max(t[7])))

# exit()

rca_std = np.std(t, axis=1, ddof=1)

# print(cga_max)
# print(cga_min)
# print(cga_avg)
# print(cga_std)

# exit()
# print(cga_std)
# print(rca_std)

x = [25, 50, 75, 100, 125, 150, 175, 200]
plt.figure(figsize=(15, 9))
# plt.plot(x, iga_min, marker='s', label='IGA_MIN', color='bisque')
# plt.plot(x, iga_max, marker='o', label='IGA_MAX', color='darkorange')
plt.plot(x, iga_avg, marker='^', label='IGA_AVG', color='orange')
# plt.plot(x, rca_min, marker='s', label='RCA_MIN', color = 'blue')
# plt.plot(x, rca_max, marker='o', label='RCA_MAX', color = 'darkblue')
plt.plot(x, rca_avg, marker='^', label='RCA_AVG', color = 'mediumblue')
# plt.plot(x, cga_min, marker='s', label='CGA_MIN', color='limegreen')
# plt.plot(x, cga_max, marker='o', label='CGA_MAX', color='darkgreen')
plt.plot(x, cga_avg, marker='^', label='CGA_AVG', color='green')
plt.xlabel("GA Generation", fontsize='xx-large')
plt.ylabel("Total Cost (€)", fontsize='xx-large')
plt.xticks(fontsize='xx-large')
plt.yticks(fontsize='xx-large')
plt.legend(prop={'size': 'xx-large'})
plt.show()

# plt.figure(figsize=(15, 9))
# plt.plot(x, iga_std, marker='d', label='IGA', color='orange')
# plt.plot(x, cga_std, marker='d', label='CGA', color='green')
# plt.plot(x, rca_std, marker='d', label='RCA', color='blue')
# plt.xlabel("GA Generation", fontsize='xx-large')
# plt.ylabel("Standard deviation (€)", fontsize='xx-large')
# plt.xticks(fontsize='xx-large')
# plt.yticks(fontsize='xx-large')
# plt.legend(prop={'size': 'xx-large'})
# plt.show()

# print(iga_std, cga_std, rca_std)
