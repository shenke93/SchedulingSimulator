import simpy

def my_proc(env):
    print('Run my_proc')
    yield env.timeout(1)
    env.exit(42)
        
def other_proc(env):
    ret_val = yield env.process(my_proc(env))
    assert ret_val == 42
    # 

env = simpy.Environment()    
env.process(other_proc(env))

