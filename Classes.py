from enum import Enum

import copy
import numpy.random as nr

epsilon = 0.5
N0 = 100.0


class Tree:
    def __init__(self):
        self.nodes = dict()

    def node_visited(self, state):
        if state.ID in self.nodes:
            self.nodes[state.ID].Ns += 1

        elif state.ID not in self.nodes:
            self.nodes[state.ID] = Node(state.ID)

        else:
            ValueError('Not a Valid State')

    def node_action_update(self, state, action):
        self.nodes[state.ID].Nsa[action] += 1


class Node:
    def __init__(self, identity):
        self.Q = {'hit': 0.0, 'stick': 0.0}
        self.Ns = 1
        self.Nsa = {'hit': 0, 'stick': 0}
        self.ID = identity
        self.eps = 1.0/self.Ns


class Card:
    def __init__(self,val, col):
        self.color = col
        self.value = val

    def get_card_value(self):
        if self.color is Color.BLACK:
            return self.value
        elif self.color is Color.RED:
            return -self.value
        else:
            ValueError('Invalid Suit')


class Color(Enum):
    BLACK = 1
    RED = 2


class Hand:
    def __init__(self, cards):
        self.cards = cards
        self.value = self.get_value()
        self.bust = self.is_bust()
        self.hand = copy.deepcopy(cards)

    def add(self):
        modified = self.hand
        modified.append(Card(nr.randint(1, 11), nr.choice(list(Color), 1, p=[(2.0/3.0), (1.0/3.0)])[0]))
        return Hand(modified)

    def get_value(self):
        result = 0
        for card in self.cards:
            result += card.get_card_value()
        return result

    def is_bust(self):
        if (self.value > 21) | (self.value < 1):
            return True
        else:
            return False


class GameState:

    def __init__(self, dealer, player):
        self.dealer = dealer
        self.player = player
        self.terminal = False
        self.ID = self.ID()

    def ID(self):
        return str(int(self.dealer.get_value())) + ' ' + str(int(self.player.get_value()))

    def state_info(self):
        information = dict()
        information['State ID'] = self.ID
        information['Number of Player Cards'] = len(self.player.cards)
        information['Number of Dealer Cards'] = len(self.dealer.cards)
        information['Player Total'] = self.player.get_value()
        information['Dealer Total'] = self.dealer.get_value()
        information['Player Cards'] = [[card.value, card.color] for card in self.player.cards]
        for k in sorted(information.keys()):
            print k, information[k]

    def stick(self):
        steps = 0.0
        mod_dealer = copy.deepcopy(self.dealer)
        while (mod_dealer.get_value() < 17.0) & (mod_dealer.bust is False) & (steps < 10.0):
            mod_dealer = mod_dealer.add()
            steps += 1
            # print (steps, mod_dealer.get_value(), mod_dealer.bust)
        new_state = GameState(mod_dealer, self.player)
        new_state.terminal = True
        return new_state


class Episode:
    def __init__(self, his):
        self.start_state = self.start_game()
        # self.interim_state = copy.deepcopy(self.start_state)
        self.states = [self.start_state]
        self.state_IDs = [self.start_state.ID]
        self.state_data = []
        self.rewards = []
        self.history = his

    def start_game(self):
        dealer = Hand([Card(nr.randint(1, 11), Color.BLACK)])
        player = Hand([Card(nr.randint(1, 11), Color.BLACK)])
        return GameState(dealer, player)

    def run(self):
        steps = 0
        while (self.states[-1].terminal == False) & (steps < 10):
            action = self.step_prep(self.states[-1])
            new_state, reward = self.step(self.states[-1], action)
            self.state_data.append([self.states[-1].ID, action, reward, new_state.ID])
            self.states.append(new_state)
            self.state_IDs.append(new_state.ID)
            self.rewards.append(reward)
            steps += 1.0
            # print steps, action, reward
            # print new_state.state_info()

    def step(self, state, action):
        reward = None
        new_state = None
        if action == 'hit':
            new_state = GameState(state.dealer, state.player.add())
            if new_state.player.bust:
                new_state.terminal = True
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

    def step_prep(self, state):
        self.history.node_visited(state)
        node = self.history.nodes[state.ID]
        eps = 1.0/node.Ns
        explore_exploit = nr.choice([0, 1], 1, p=[1.0 - eps,  eps])[0]
        max_action = max(node.Q, key=node.Q.get)
        if explore_exploit == 1:
            node.Nsa[max_action] += 1.0
            return max_action
        else:
            keys = node.Q.keys()
            keys.pop(keys.index(max_action))
            action = nr.choice(keys)
            node.Nsa[action] += 1.0
            return action










