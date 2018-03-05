import simpy

def my_callback(event):
    print('Run')
    print('Called back from', event)
    
env = simpy.Environment()
event = env.event()
event.callbacks.append(my_callback)
# event.callbacks[0](event)

