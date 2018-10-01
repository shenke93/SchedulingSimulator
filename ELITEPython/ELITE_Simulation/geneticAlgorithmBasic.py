import numpy as np
import csv
from datetime import timedelta, datetime

DNA_SIZE = 5    
POP_SIZE = 4   
CROSS_RATE = 0.3
MUTATION_RATE = 0.2
N_GENERATIONS = 100

def ceil_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q+1)*delta) if r else dt

def floor_dt(dt, delta):
    q, r = divmod(dt - datetime.min, delta)
    return (datetime.min + (q)*delta) if r else dt

def get_energy_cost(indiviaual, start_time, job_dict, price_dict):
    ''' Give an individual (a possible schedule in our case), calculate its energy cost '''
    energy_cost = 0
    t_now = start_time # current timestamp
    for item in indiviaual:
#         print("\nFor job: %d" % item)
        t_start = t_now
#         print("Time start: " + str(t_now))
        du = job_dict.get(item, -1)[0] # get job duration
        po = job_dict.get(item, -1)[1] # get job power profile
        # TODO: if get duration failed (du == -1), handle this situation
        t_end = t_start + timedelta(hours=du)
#         print("Time end: " + str(t_end))
        
        # calculate sum of head price, tail price and body price

        t_u = ceil_dt(t_start, timedelta(hours=1))
        t_d = floor_dt(t_end, timedelta(hours=1)) 
#         print("Ceil time start to the next hour:" + str(t_u))
#         print("Floor time end to the previous hour:" + str(t_d))
        tmp = price_dict.get(floor_dt(t_now, timedelta(hours=1)), 0)*((t_u - t_start)/timedelta(hours=1)) +  price_dict.get(t_d, 0)*((t_end - t_d)/timedelta(hours=1))
        tmp = tmp * po
#         print("Head price: %f" % price_dict.get(floor_dt(t_now, timedelta(hours=1)), 0))
#         print("Tail price: %f" % price_dict.get(t_d, 0))
#         print("Head and tail cost: %f" % tmp)
        step = timedelta(hours=1)
        while t_u < t_d:
            energy_cost += price_dict.get(t_u, 0) * po
            t_u += step
        
        energy_cost += tmp
        t_now = t_end
    
    return energy_cost

def get_fitness(pred):
    ''' Calculate the fitness of every individual in a generation.
    Simple strategy: Keep the Elitism in the new generation, also remeber the Elitism
    '''
    return np.max(pred) + 1e-3 - pred
    
def select(pop, fitness):
    ''' Nature selection with individuals' fitnesses.
    '''
    idx = np.random.choice(np.arange(POP_SIZE), size=POP_SIZE, replace=True, p = fitness/fitness.sum())
#     print("idx:", idx)
    return pop[idx] 
    
def crossover(parent, pop):
    if np.random.rand() < CROSS_RATE:
        i_ = np.random.randint(0, POP_SIZE,size=1) # select another individual from pop
#         print("i_: ", i_)
        cross_points = np.random.randint(0, 2, DNA_SIZE).astype(np.bool) # choose crossover points
        keep_city = parent[~cross_points]
#         print("keep_city: ", keep_city)
#         print("pop[i_]: ", pop[i_])
#         print("choose: ", np.isin(pop[i_].ravel(), keep_city, invert=True))
        swap_city = pop[i_, np.isin(pop[i_].ravel(), keep_city, invert=True)]
        parent[:] = np.concatenate((keep_city, swap_city))
    return parent
    
def mutate(child):
    ''' Find two different points of DNA, change their order
    '''
    for point in range(DNA_SIZE):
        if np.random.rand() < MUTATION_RATE:
            swap_point = np.random.randint(0, DNA_SIZE)
            swap_A, swap_B = child[point], child[swap_point]
            child[point], child[swap_point] = swap_B, swap_A
    return child

if __name__ == '__main__':
    
    start_time = datetime(2016, 11, 7, 1, 0)
    price_dict = {}
    job_dict = {}
    
    # TODO: handle exceptions: file not exist etc.
    ''' Input: Energy price
        Input file: price_ga.csv
        format: date(date), price(float)
    '''
    with open('price_ga.csv', encoding='utf-8') as price_csv:
        reader = csv.DictReader(price_csv)
        for row in reader:
            price_dict.update({datetime.strptime(row['Date'], "%Y-%m-%d %H:%M:%S"):float(row['Euro'])})

    ''' Input: List of jobs (original schedule)
        Input file: jobInfo_ga.csv
        format: index(int), duration(float), power(float)
    '''
    with open('jobInfo_ga.csv', encoding='utf-8') as jobInfo_csv:
        reader = csv.DictReader(jobInfo_csv)
        for row in reader:
            job_dict.update({int(row['ID']):[float(row['Duration']), float(row['Power'])]})
     
    print(price_dict)        
    print(job_dict)        
 
    # We use an individual for test: 
#     arr = np.arange(1, 6)
#     np.random.shuffle(arr)
#     print(arr)
    
#     print(get_fitness(arr, start_time, job_dict, price_dict))
    pop = np.vstack([np.random.permutation(range(1, 6)) for _ in range(POP_SIZE)])
#     print(pop)
    
    '''Optimization possibility 1: Add maintenance events.
        Rules: 1. 
    '''
    
    '''Optimization possibility 2: From Xu's paper, machine different power states.
        Rules: 
    '''
    
    ''' Optimization possibility 3: Job with different power profile.
    '''
    
    for n in range(N_GENERATIONS):
        print("\nIn Generation %d: " % n)
        cost = [get_energy_cost(ind, start_time, job_dict, price_dict) for ind in pop]
        print(cost)
    
        fitness = get_fitness(cost)
        print(pop)
        print("Most fitted DNA: ", pop[np.argmax(fitness)])
        print("Most fitted cost: ", cost[np.argmax(fitness)])

        pop = select(pop, fitness)
#         print("New generation: ", pop)
    
        pop_copy = pop.copy()
        for parent in pop:
#             print("Parent: ", parent)
            child = crossover(parent, pop_copy)
#             print("Child: ", child)
            child = mutate(child)
            parent[:] = child
            
    