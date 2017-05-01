import numpy.random as nr
import numpy as np

from Classes import *

from MCC import *


def start_game():
    dealer = Hand([Card(nr.randint(1, 11), Color.BLACK)])
    player = Hand([Card(nr.randint(1, 11), Color.BLACK)])
    return GameState(dealer, player)


def step(state, action):
    reward = None
    new_state = None
    if action == 'hit':
        new_state = GameState(state.dealer, state.player.add())
        if new_state.player.bust:
            new_state.terminal= True
            reward = -1.0
        else:
            reward = 0.0

    elif action == 'stick':
        new_state = state.stick()
        if new_state.dealer.bust:
            reward = 1.0
        elif new_state.player.get_value() > new_state.dealer.get_value():
            reward = 1.0
        elif new_state.player.get_value() == new_state.dealer.get_value():
            reward = 0.0
        elif new_state.player.get_value() < new_state.dealer.get_value():
            reward = -1.0
    else:
        ValueError('Invalid Action passed to Step function')
    return new_state, reward


history = Tree()


# ep = Episode(history)
# ep.run()
# print ep.state_IDs
# print ep.rewards
#
# MonteCarloControl(ep, history)
#
# for i, st_id in enumerate(ep.state_IDs[:-1]):
#     print st_id, history.nodes[st_id].Q, ep.state_data[i][1]

for n in range(1000):
    ep = Episode(history)
    ep.run()
    MonteCarloControl(ep, history)

for node in sorted(history.nodes):
    if history.nodes[node].Ns > 1:
        print node, history.nodes[node].Q, history.nodes[node].Ns