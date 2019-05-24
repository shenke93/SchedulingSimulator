import numpy as np

def calculate_fitness(pop):
    ''' 
    Fitness calculation function for an individual.
    Dependent on problem scenarios.
    '''
    return np.array([ np.array(i[0]) for i in pop ])

class GA():
    def __init__(self, start_individual, nb_generation, size_individual, size_population, cross_rate, mutation_rate,
                 calculate_fitness_pop, 
                 num_mutations=1, selection_method='roulette', mutation_mode='basic', pre_selection=False):
        ''' 
        Basic setting of an abstract genetic algorithm.
        Parameters: nb_generation: number of generations; size_induvidual: number of genes in a chromosome (individual);
        size_population: number of individuals in a population; cross_rate: rate for crossover; mutation_rate: rate for mutation;
        num_mutations: number of mutations to apply; evolution_method: method for selection; pre_selection: flag for selection. 
        '''
        self.nb_generation = nb_generation
        self.size_individual = size_individual
        self.size_population = size_population
        self.cross_rate = cross_rate
        self.mutation_rate = mutation_rate
        self.num_mutations = num_mutations
        self.selection_method = selection_method
        self.mutation_mode = mutation_mode
        self.pre_selection = pre_selection
        
        # Population initialization
        self.initial_population(start_individual)
        self.set_fitness_pop(calculate_fitness_pop)
#         # Unit test for population initialization
#         print("self.pop:", self.pop)
#         print("type(self.pop), type(self.pop[0]):", type(self.pop), type(self.pop[0]))
        
#         self.memory = []  # Possible to add memory support
    
    
    def initial_population(self, start_individual):
        ''' 
        Initialization of the start population according to a given start individual.
        '''
        if self.pre_selection == True:
            # If the pre-selection policy has already been applied to the start_individual.
            # Initialize a pop from an individual.
            # pop = [ individual * pop_size]
            # Example: i1 = [1, 2, 3]; pop = [ i1, i1, i1]
            # Using ndarray
            self.pop = np.vstack(start_individual for _ in range(self.size_population))
        else:
            # If no pre-selction policy is applied, use random initialization.
            # pop = [ individual * pop_size]
            # Example: i1 = [1, 2, 3]; pop = [[1, 2, 3], [2, 1, 3], [2, 3, 1]
            # Using ndarray
            self.pop = np.vstack([np.random.choice(start_individual, size=self.size_individual, replace=False) 
                                  for _ in range(self.size_population)])
        
    def set_fitness_pop(self, calculate_fitness_pop):
        '''
        Use the fitness calculation function declared outside.
        Get fitness for one individual.
        '''
        self.generation_fitness_cal = calculate_fitness_pop
    
    def crossover(self, winner_loser):
        '''
        Using microbial genetic evolution strategy. The winner is kept as the elitist. 
        The loser is replaced by the result of crossover.
        '''

        if np.random.rand() < self.cross_rate:
            # Mask based crossover
            # Using numpy array manipulations
            cross_points = np.random.randint(0, 2, self.size_individual, dtype=np.bool)
#             print('cross_points:', cross_points) # Test code
            keep_jobs = winner_loser[1][~cross_points]
#             print('keep_jobs:', keep_jobs) # Test code
            swap_jobs = winner_loser[0][np.isin(winner_loser[0].ravel(), keep_jobs, invert=True)]
#             print('swap_jobs:', swap_jobs) # Test code
            winner_loser[1][:] = np.concatenate((keep_jobs, swap_jobs))
#             print('loser:', winner_loser[1])
        
#         print('winner_loser (after crossover):', winner_loser)    
        return winner_loser
    
    
    def mutate(self, winner_loser): 
        ''' Using microbial genetic evolution strategy, mutation only works on the loser.
        '''
        # mutation for loser, randomly choose two points and do the swap
        if np.random.rand() < self.mutation_rate:
            point, swap_point = np.random.randint(0, self.size_individual, size=2)
#             print('point, swap_point:', point, swap_point)
            swap_A, swap_B = winner_loser[1][point], winner_loser[1][swap_point]
            winner_loser[1][point], winner_loser[1][swap_point] = swap_B, swap_A 
        
#         print('winner_loser (after mutation):', winner_loser)
        return winner_loser
        
            
    def evlove(self):
        '''
        Execution (workflow) of the genetic algorithm.
        '''
        if self.selection_method == 'roulette':
            # Sort all individuals in a generation according to their fitnesses.
            print('Currently not implemented, no such selection method.')
            exit()     
        else:
            # Randomly choose two individuals. 
            picked_idx = np.random.choice(np.arange(0, self.size_population), size=2, replace=False)
#             print("picked_idx:", picked_idx) # Test code

        # Pick two individuals and calculate their fitnesses.   
        picked_pop = self.pop[picked_idx]
#         print("picked_pop:", picked_pop) # Test code
        picked_pop_fitness = self.generation_fitness_cal(picked_pop)
#         print("picked_pop_fitness:", picked_pop_fitness) # Test code
#         exit() # Test break
        
        # Sort two individuals by fitness
        # winner has lower fitness than loser
        winner_loser_idx = np.argsort(picked_pop_fitness)
        winner_loser = picked_pop[winner_loser_idx]
#         print('winner_loser (before genetic operations):', winner_loser) # Test code
#         exit() # Test break

        # Do crossover and mutation
        winner_loser = self.crossover(winner_loser)
#         exit() # Test break
        winner_loser = self.mutate(winner_loser)
        
        # Merge changes into the generation
        self.pop[picked_idx] = winner_loser
        
        return self.pop
    
    
if __name__ == '__main__':
    ind_start = [1, 2, 3, 4, 5, 6, 7, 8]
    np.random.seed(20)
    ga1 = GA(start_individual=ind_start, nb_generation=10, size_individual=8, size_population=4, cross_rate=1, mutation_rate=1,
             calculate_fitness_pop=calculate_fitness, num_mutations=1, selection_method='random', pre_selection=False)
    ga1.evlove()