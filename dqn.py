from torch import nn
import torch
from collections import deque
import itertools
import numpy as np
import random
from tetris import Tetris
import pygame
import matplotlib.pyplot as plt


GAMMA = 0.7
BATCH_SIZE = 32
BUFFER_SIZE = 10000
MIN_REPLAY_SIZE = 100
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY = 5000
TARGET_UPDATE_FREQ = 100
LEARNING_RATE = 1e-4

REW_BUFFER_LENGTH = 10

NUM_INPUTS = 4
INPUT_TIMES = 80
NUM_OUTPUTS = 1
OUTPUT_TIMES = 80
VIEWING_THRESHOLD = 5000


#Create class for neural networks
class Network(nn.Module):
    def __init__(self, env):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(NUM_INPUTS, 4), nn.ReLU(), nn.Linear(4, NUM_OUTPUTS))
    
    def forward(self, x):
        return self.net(x)
    
    def forwardBreakdown(self, obses_t):
        
        # all_q_values = torch.zeros(BATCH_SIZE,INPUT_TIMES)
        # for i in range(BATCH_SIZE):
        #     obs_t = torch.as_tensor(obses[i], dtype=torch.float32).view(-1, NUM_INPUTS)
        #     for j in range(INPUT_TIMES):
        #         all_q_values[i,j] = self(obs_t[j].unsqueeze(0))[0]
        #return all_q_values
        
        obs_t = torch.as_tensor(obses, dtype=torch.float32).view(BATCH_SIZE * INPUT_TIMES, NUM_INPUTS)
        q_values = self(obs_t).view(BATCH_SIZE, INPUT_TIMES)
        return q_values
        
    
    def act(self, obs):
        obs_t = torch.as_tensor(obs, dtype=torch.float32).view(-1, NUM_INPUTS)
        # q_values = []
        
        # for i in range(INPUT_TIMES):
        #     q_values.append(self(obs_t[i].unsqueeze(0)).tolist()[0])
        
        # max_q_index = q_values.index(max(q_values))
        # action = max_q_index
        
        with torch.no_grad():
            q_values = self(obs_t).squeeze(1).tolist()

        action = np.argmax(q_values)
        
        return action

clock = pygame.time.Clock()

#Initialize environment (Tetris game)
env = Tetris()

#Create container for storing recent experiences and rewards
replay_buffer = deque(maxlen = BUFFER_SIZE)
rew_buffer = deque([0,0], maxlen=REW_BUFFER_LENGTH)
rew_tracker = [1000]

episode_reward = 0.0

#Initialize main and target neural networks
online_net = Network(env)
target_net = Network(env)

target_net.load_state_dict(online_net.state_dict())

optimizer = torch.optim.Adam(online_net.parameters(), lr = LEARNING_RATE)

#Initialize Replay Buffer
print("initializing replay buffer")
obs, _ = env.reset()
for _ in range(MIN_REPLAY_SIZE):
    print(".",end="")
    action = env.getRandomAction()
    
    new_obs, rew, done = env.step(action)
    replay_buffer.append((obs, action, rew, done, new_obs))
    obs = new_obs if not done else env.reset()[0]
        
#Main training loop
obs, _ = env.reset()

for step in itertools.count():
    print(".",end="")
    epsilon = np.interp(step, [0, EPSILON_DECAY], [EPSILON_START, EPSILON_END])
    
    rnd_sample = random.random()
    
    if rnd_sample <= epsilon:
        action = env.getRandomAction()
    else:
        action = online_net.act(obs)
        
    new_obs, rew, done = env.step(action)
    transition = (obs, action, rew, done, new_obs)
    replay_buffer.append(transition)
    obs = new_obs
    
    episode_reward += rew
    
    if done:
        obs, _ = env.reset()
        
        rew_buffer.append(episode_reward)
        rew_tracker.append(episode_reward)
        episode_reward = 0.0
        
    #After Solved, watch it play
    if len(rew_buffer) >= 5:
        #clock.tick(120)
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE] or [pygame.K_r] or [pygame.K_d] or np.mean(rew_buffer) >= VIEWING_THRESHOLD:
            while keys[pygame.K_SPACE] or np.mean(rew_buffer) >= VIEWING_THRESHOLD:
                clock.tick(60)
                action = online_net.act(obs)
                
                obs, _, done = env.step(action)
                
                env.drawWindow()
                if done:
                    env.reset()
                    
                keys = pygame.key.get_pressed()
            
            while keys[pygame.K_r]:
                clock.tick(60)
                rnd_sample = random.random()
    
                if rnd_sample <= epsilon:
                    action = env.getRandomAction()
                else:
                    action = online_net.act(obs)
                
                obs, _, done = env.step(action)
                
                env.drawWindow()
                if done:
                    env.reset()
                    
                keys = pygame.key.get_pressed()
            
            if keys[pygame.K_d]:
                plt.plot(rew_tracker[1:])
                plt.title("Rewards")
                plt.show()
            
            
    
    #Start gradient step
    transitions = random.sample(replay_buffer, BATCH_SIZE)

    obses = np.asarray([t[0] for t in transitions])
    actions = np.asarray([t[1] for t in transitions])
    rews = np.asarray([t[2] for t in transitions])
    dones = np.asarray([t[3] for t in transitions])
    new_obses = np.asarray([t[4] for t in transitions])
    
    obses_t = torch.as_tensor(obses, dtype = torch.float32)
    actions_t = torch.as_tensor(actions, dtype = torch.int64).unsqueeze(-1)
    rews_t = torch.as_tensor(rews, dtype = torch.float32).unsqueeze(-1)
    dones_t = torch.as_tensor(dones, dtype = torch.float32).unsqueeze(-1)
    new_obses_t = torch.as_tensor(new_obses, dtype = torch.float32)
    
    
    #Compute targets
    target_q_values = target_net.forwardBreakdown(new_obses_t)
    max_target_q_values = torch.max(target_q_values, dim=1)[0].unsqueeze(1)

    targets = rews_t + GAMMA*(1-dones_t)*max_target_q_values
    
    #Compute losss
    q_values = online_net.forwardBreakdown(obses_t)
    
    action_q_values = q_values.gather(1, actions_t)
    loss = nn.functional.smooth_l1_loss(action_q_values, targets)
    
    #Gradient descent
    optimizer.zero_grad()
    loss.backward()
    torch.nn.utils.clip_grad_norm_(online_net.parameters(), max_norm=1.0)
    optimizer.step()
    
    #Update target network
    if step % TARGET_UPDATE_FREQ == 0:
        target_net.load_state_dict(online_net.state_dict())
        
    #Logging
    if step % TARGET_UPDATE_FREQ == 0:
        print()
        print('Step', step)
        print('Avg Rew', np.mean(rew_buffer))