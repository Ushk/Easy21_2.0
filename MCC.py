from Classes import *

def MonteCarloControl(ep, history):

    for i, st_id in enumerate(ep.state_IDs[:-1]):
        node = history.nodes[st_id]
        action = ep.state_data[i][1]
        node.Q[action] += (1.0/node.Nsa[action])*(ep.rewards[-1] - node.Q[action])

