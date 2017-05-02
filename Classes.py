from enum import Enum

import copy
import numpy.random as nr

epsilon = 0.5
N0 = 100.0


class Tree:
    """
    The tree class maps the state space. Each node is associated with a game state via a state ID. This is stored in a
    dict, where each key is a state ID and each value is a Node.
    """
    def __init__(self):
        self.nodes = dict()

    def node_visited(self, state):
        """
        This function generates a node, if the state has not been observed before, or increments by 1 the number visits
        if the state has been visited before.
        :param state: The current GameState, to be checked.
        :return: Null
        """
        if state.ID in self.nodes:
            self.nodes[state.ID].Ns += 1

        elif state.ID not in self.nodes:
            self.nodes[state.ID] = Node(state.ID)

        else:
            ValueError('Not a Valid State')

    def node_action_update(self, state, action):
        """
        This function updates the number of times an action was taken from that particular state. This is not useful
        for MCC, but will be used in the next Step.
        :param state: The current GameState.
        :param action: The action taken from that GameState.
        :return: Null
        """
        self.nodes[state.ID].Nsa[action] += 1


class Node:
    """
    Each node represents a node on the tree that is being used to map the state space. It is used to record the variables
    needed for learning between Episodes.
    """
    def __init__(self, identity):
        """
        :param identity: The ID is the ID of the GameState associated with the node. It is used to link Nodes
        with GameStates.
        Q - The Action-Value function. It represents the expected reward from each available action in the state.
        Ns - The number of times a state has been visited.
        Nsa - The number of times each action has been taken from that state.
        eps - The appropriate epsilon for the next action (actions are chosen accoring to an e-greedy strategy
        """
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
    """
    A Hand represents a set of cards. The hand has a value, which is the card values appropriately summed according to
    their color.
    A hand can be bust, which occurs if the overall value of the hand is <= 0 or >= 21.
    """
    def __init__(self, cards):
        self.cards = cards
        self.value = self.get_value()
        self.bust = self.is_bust()
        self.hand = copy.deepcopy(cards)  # This copy is potentially unnecessary... it is to ensure the original set of
                                          # cards is unchanged.

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
    """
    A GameState represents a state in the game (duh). It consists of a dealer's hand and a player's hand.
    The dealer will only show 1 card, while the player starts with one and has the option of drawing more.
    If the player 'hits' they draw another card. If the player 'sticks', the dealer will draw.
    A player can go bust if their hand goes below 1 or above 21
    A dealer will always draw unless their hand 17 or greater. They can go bust according to the same criteria as a
    player
    A state is terminal if the player goes bust or sticks
    A state has an ID, which is used to uniquely identify it. The ID uses the format {dealers hand's value players
    hand's value}
    Note that we treat two states with different cards, but the same dealer and player hand values as the same state.
    This is because the Q-function will be identical for those two states.
    """

    def __init__(self, dealer, player):
        self.dealer = dealer
        self.player = player
        self.terminal = False
        self.ID = self.ID()

    def ID(self):
        return str(int(self.dealer.get_value())) + ' ' + str(int(self.player.get_value()))

    def state_info(self):
        """
        This function is mainly used to debug the GameState. It is a convenient way of displaying State information.
        :return: Null
        """
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
    """
    An Episode is a game of Easy21. It starts with a start state, then runs until it reaches a terminal state.
    The states and rewards are tracked, and used to learn how to play the game to receive a higher reward.
    """
    def __init__(self, his):
        """
        :param his: The Tree, containing all of the nodes visited so far.
        """
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
        """
        This function takes the Episode start state and runs it until a terminal state is reached.
        :return: Null
        """
        steps = 0
        while (self.states[-1].terminal == False) & (steps < 10):  # Steps is to cap the number of iterations
            action = self.step_prep(self.states[-1])  # Action is chosen
            new_state, reward = self.step(self.states[-1], action)  # New state and reward are generated
            self.state_data.append([self.states[-1].ID, action, reward, new_state.ID])
            self.states.append(new_state)
            self.state_IDs.append(new_state.ID)
            self.rewards.append(reward)
            steps += 1.0
            # print steps, action, reward
            # print new_state.state_info()

    def step(self, state, action):
        """
        This function takes a state and action, and uses these to return a new state, with some associated reward.
        See the game rules for rules on how rewards are generated.
        :param state: The initial state
        :param action: The action that the agent takes from this state ('hit'/'stick'). Note that the stick action makes
        the state terminal, whereas hit only does this if the player goes bust.
        :return: new_state: The new state generated by taking the action
        :return: reward: the reward from taking the action.
        """
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
        """
        This function prepares for the Step to take place. It handles updating the Node, generating the correct Epsilon
        and choosing an action.
        :param state:
        :return: action: The action to be taken from that state.
        """
        self.history.node_visited(state)  # Has this node been visited.
        node = self.history.nodes[state.ID]
        eps = N0/(N0 + node.Ns)  # Generate epsilon. Note that it will go to zero as the state is visited more times.
        explore_exploit = nr.choice([0, 1], 1, p=[1.0 - eps,  eps])[0]  # Chose whether to explore/exploit
        max_action = max(node.Q, key=node.Q.get)  # Get action with max exp reward.
        if explore_exploit == 1:  # Exploit - choose action with highest reward.
            node.Nsa[max_action] += 1.0
            return max_action
        else:  # Explore - choose a non-ideal action at random.
            keys = node.Q.keys()
            keys.pop(keys.index(max_action))  # Remove max value.
            action = nr.choice(keys)
            node.Nsa[action] += 1.0
            return action










