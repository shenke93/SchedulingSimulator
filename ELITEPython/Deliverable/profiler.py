import cProfile
import execute
import pstats

retry = True

if retry:
    cProfile.run('execute.main()', 'restats.txt')

pstats.Stats('restats.txt').sort_stats('tottime').print_stats(.01)