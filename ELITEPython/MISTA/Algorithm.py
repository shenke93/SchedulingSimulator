import numpy as np
class GA():
    def __init__(self, start_individual, nb_generation, size_individual, size_population, cross_rate, mutation_rate, 
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
#         # Unit test for population initialization
#         print("initial_population:", self.pop)
#         print("initial_population type:", type(self.pop), type(self.pop[0]))
        
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
        
    def get_fitness(self):
        '''
        The default fitness calculation method. 
        Should be replaced according to the problem.
        '''
        pass
            
    def crossover(self, winner_loser):
        '''
        Using microbial genetic evolution strategy. The winner is kept as the elitist. 
        The loser is replaced by the result of crossover.
        '''
        # TODO: To be tested!
        if np.random.rand() < self.cross_rate:
            # Mask based crossover
            # Using numpy array manipulations
            cross_points = np.random.randint(0, 2, self.size_individual).astype(np.bool)
            keep_jobs = winner_loser[1][~cross_points]
            swap_jobs = winner_loser[0][np.isin(winner_loser[0].ravel(), keep_jobs, invert=True)]
            winner_loser[1][:] = np.concatenate((keep_jobs, swap_jobs))
        return winner_loser
    
    
    def mutate(self, loser):
        '''
        Mutation is only applied on the loser.
        '''
        if np.random.rand() < self.mutation_rate:
            if self.mutation_mode == 'basic':
                point, swap_point = np.random.choice(range(self.size_individual), size=2, replace=False)
            else:
                print('Currently not implemented, no mutation operation applied.')
                exit()
            swap_A, swap_B = loser[point], loser[swap_point]
            loser[point], loser[swap_point] = swap_B, swap_A
        return loser
        
            
    def evlove(self):
        if self.selection_method == 'roulette':
            fitness = self.get_fitness(self.pop)
            self.pop = self.pop[np.argsort(fitness)]           
        else:
   
        
    
    
if __name__ == '__main__':
    ind_start = [1, 2, 3, 4, 5, 6, 7, 8]
    ga1 = GA(start_individual=ind_start, nb_generation=10, size_individual=8, size_population=4, cross_rate=1, mutation_rate=1, 
                 num_mutations=1, selection_method='roulette', pre_selection=False)
    