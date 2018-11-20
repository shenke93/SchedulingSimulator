import pickle

# Getting back objects
with open('data_IGA.pkl', 'rb') as f:
    iga_raw, iga_avg, iga_min, iga_max = pickle.load(f)

with open('data_CGA.pkl', 'rb') as f:
    cga_raw, cga_avg, cga_min, cga_max = pickle.load(f)
    
with open('data_RCA.pkl', 'rb') as f:
    rca_raw, rca_avg, rca_min, rca_max = pickle.load(f)