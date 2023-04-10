import numpy as np
import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam
import matplotlib.pyplot as plt
import Druid.Balance.BalanceEnv
import time



class DQNAgent:
    def __init__(self, state_size, action_size):
        self.n_actions = action_size
        # we define some parameters and hyperparameters:
        # "lr" : learning rate
        # "gamma": discounted factor
        # "exploration_proba_decay": decay of the exploration probability
        # "batch_size": size of experiences we sample to train the DNN
        self.lr = 0.001
        self.gamma = 0.99
        self.exploration_proba = 1.0
        self.exploration_proba_decay = 0.1 
        self.batch_size = 256
        
        # We define our memory buffer where we will store our experiences
        # We stores only the 2000 last time steps
        self.memory_buffer= list()
        self.max_memory_buffer = 16384
        
        # We creaate our model having to hidden layers of 24 units (neurones)
        # The first layer has the same size as a state size
        # The last layer has the size of actions space
        self.model = Sequential([
            Dense(units=24,input_dim=state_size, activation = 'relu'),
            Dense(units=24,activation = 'relu'),
            Dense(units=action_size, activation = 'linear')
        ])
        self.model.compile(loss="mse",
                      optimizer = Adam(learning_rate=self.lr))
        
    # The agent computes the action to perform given a state 
    def compute_action(self, current_state, actions):
        # We sample a variable uniformly over [0,1]
        # if the variable is less than the exploration probability
        #     we choose an action randomly
        # else
        #     we forward the state through the DNN and choose the action 
        #     with the highest Q-value.
        if np.random.uniform(0,1) < self.exploration_proba:
            action =  np.random.choice(list(actions.keys()))
        else:
            q_values = self.model.predict(current_state, verbose=0)[0]
            poss_actions = [(ind, q_values[ind]) for ind in range(len(q_values)) if ind in actions.keys()]

            action = max(poss_actions, key=lambda action: action[1])[0]
            x=1
        return action

    # when an episode is finished, we update the exploration probability using 
    # espilon greedy algorithm
    def update_exploration_probability(self):
        self.exploration_proba = self.exploration_proba * np.exp(-self.exploration_proba_decay)
        # print(self.exploration_proba)
    
    # At each time step, we store the corresponding experience
    def store_episode(self,current_state, action, reward, next_state, done):
        #We use a dictionnary to store them
        self.memory_buffer.append({
            "current_state":current_state,
            "action":action,
            "reward":reward,
            "next_state":next_state,
            "done" :done
        })
        # If the size of memory buffer exceeds its maximum, we remove the oldest experience
        if len(self.memory_buffer) > self.max_memory_buffer:
            self.memory_buffer.pop(0)
    

    # At the end of each episode, we train our model
    def train(self):
        # We shuffle the memory buffer and select a batch size of experiences
        np.random.shuffle(self.memory_buffer)
        batch_sample = self.memory_buffer[0:self.batch_size]
        
        # We iterate over the selected experiences
        for experience in batch_sample:
            # We compute the Q-values of S_t
            q_current_state = self.model.predict(experience["current_state"], verbose=0)
            # We compute the Q-target using Bellman optimality equation
            q_target = experience["reward"]
            if not experience["done"]:
                q_target = q_target + self.gamma*np.max(self.model.predict(experience["next_state"], verbose=0)[0])
            q_current_state[0][experience["action"]] = q_target
            # train the model
            self.model.fit(experience["current_state"], q_current_state, verbose=0)

if __name__ == "__main__":
    # We create our gym environment 
    env = Druid.Balance.BalanceEnv.BalanceDruidEnvironment(haste = 954,
                                    critical_strike=262, 
                                    versatility=311,
                                    mastery=1318,
                                    main_stat=2835) 

    # We get the shape of a state and the actions space size
    print("Done")
    state_size = len(env.get_state())
    action_size = len(env.get_actions())
    # Number of episodes to run
    n_episodes = 20
    # Max iterations per epiode
    max_iteration_ep = 31000
    # We define our agent
    agent = DQNAgent(state_size, action_size)
    total_steps = 0
    max_reward = 0
    # We iterate over episodes

    start_time = time.time()
    for e in range(n_episodes):
        # We initialize the first state and reshape it to fit 
        #  with the input layer of the DNN
        print("Current Episode:", e)
        rewards = []
        current_state = env.reset()
        current_state = np.array([current_state])
        action_sequence = []
        episode_time = time.time()
        for step in range(max_iteration_ep):
            total_steps = total_steps + 1
            # the agent computes the action to perform
            actions = env.get_actions()

            if len(actions) == 0:
                action = -1
            elif len(actions) == 1:
                action = list(actions.keys())[0]
            else:
                action = agent.compute_action(current_state, actions)

            # the envrionment runs the action and returns
            # the next state, a reward and whether the agent is done
            prev_ap = env.astral_power.current
            next_state, reward, done = env.step(action)
            next_state = np.array([next_state])

            rewards.append(reward)

            # We sotre each experience in the memory buffer
            agent.store_episode(current_state, action, reward, next_state, done)
            
            # if the episode is ended, we leave the loop after
            # updating the exploration probability
            if done:
                agent.update_exploration_probability()
                break
            current_state = next_state
        # if the have at least batch_size experiences in the memory buffer
        # than we tain our model
        episode_end_time = time.time()
        if total_steps >= agent.batch_size:
            train_time = time.time()
            agent.train()
        print("Episode Training Time: ", episode_end_time - episode_time)
        print("Training Time:", time.time() - train_time)

    print("Total training time: ", time.time() - start_time)
    model_json = agent.model.to_json()
    with open("model.json", "w") as json_file:
        json_file.write(model_json)

    env = Druid.Balance.BalanceEnv.BalanceDruidEnvironment(haste = 954,
                                    critical_strike=262, 
                                    versatility=311,
                                    mastery=1318,
                                    main_stat=2835) 

    print("Begin Testing")

    done = False
    agent.exploration_proba = 0
    reward = 0

    current_state = env.reset()
    current_state = np.array([current_state])
    while not done:
        actions = env.get_actions()

        if len(actions) == 0:
            action = -1
        elif len(actions) == 1:
            action = list(actions.keys())[0]
        else:
            action = agent.compute_action(current_state, actions)

        next_state, reward, done = env.step(action)
        next_state = np.array([next_state])

        #if action != -1:
            #print(actions[action], env.env_timer.current_time, current_state, reward)
        
        current_state = next_state

    print(env.total_damage / 300)

    results = dict(sorted(env.results.items(), key=lambda item: item[1][0], reverse=True))

    txt = "{spell:20} \t {damage:10.2f} \t {casts:4}"
    for key, value in results.items():
        print(txt.format(spell=key, damage=value[0], casts=value[1]))

    ax1 = plt.subplot(4,1,1)
    ax1.scatter(np.arange(len(env.ap_chart))/100, env.ap_chart, s=2, c='b')
    ax2 = plt.subplot(4,1,2)
    ax2.plot(np.arange(len(env.incarn_active))/100, env.incarn_active)
    ax6 = plt.subplot(4,1,2)
    ax6.plot(np.arange(len(env.rf_chart))/100, env.rf_chart)
    ax3 = plt.subplot(4,1,3)
    ax3.plot(np.arange(len(env.lunar_eclipse_chart))/100, env.lunar_eclipse_chart)
    ax4 = plt.subplot(4,1,4)
    ax4.plot(np.arange(len(env.solar_eclipse_chart))/100, env.solar_eclipse_chart)
    ax5 = plt.subplot(4,1,1)
    p_chart = [pc / 3 for pc in env.pulsar_chart]
    ax5.scatter(np.arange(len(p_chart))/100, p_chart, s=2, c='r')

    plt.show()