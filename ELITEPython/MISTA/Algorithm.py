import numpy as np
class GA():
    def __init__(self, start_individual, nb_generation, size_individual, size_population, cross_rate, mutation_rate, 
                 num_mutations=1, selection_method='roulette', pre_selection=False):
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
        self.pre_selection = pre_selection
        
        # Population initialization
        self.initial_population(start_individual)
        
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
            self.pop = np.vstack(start_individual for _ in range(self.size_population))
        else:
            # If no pre-selction policy is applied, use random initialization.
            # pop = [ individual * pop_size]
            # Example: i1 = [1, 2, 3]; pop = [[1, 2, 3], [2, 1, 3], [2, 3, 1]
            self.pop = np.vstack([np.random.choice(start_individual, size=self.size_individual, replace=False) 
                                  for _ in range(self.size_population)])
        
        
    def crossover(self, winner_loser):
        '''
        Using microbial genetic evolution strategy. The winner is kept as the elitist. 
        The loser is replaced by the result of crossover.
        '''
        if np.random.rand() < self.cross_rate:
            # Mask based crossover
            # Using numpy array manipulations
            cross_points = np.random.randint(0, 2, self.size_individual).astype(np.bool)
            keep_jobs = winner_loser[1][~cross_points]
            swap_jobs = winner_loser[0, np.isin(winner_loser[0].ravel(), keep_jobs, invert=True)]
            
        return winner_loser