import os
import boto3
import json
import numpy as np

from agent import DQNAgent
from Druid.Balance.BalanceEnv import BalanceDruidEnvironment

try:
    bucketName = os.environ['BUCKET_NAME']
except:
    bucketName = 'dps-sim-models'

s3 = boto3.client('s3')

def handler(event, context):
    #response = s3.get_object(Bucket=bucketName, Key='model.json')
    #content = response['Body']

    #json_obj = json.loads(content.read())

    return {
        'statusCode': 200,
        'body': json.dumps({"Report": "Ran"}, indent=2)
    }

    env = BalanceDruidEnvironment(haste=event.haste,
                                  critical_strike=event.critical_strike, 
                                  versatility=event.versatility,
                                  mastery=event.mastery,
                                  main_stat=event.main_stat) 
    
    state_size = len(env.get_state())
    action_size = len(env.get_actions())

    agent = DQNAgent(state_size, action_size)
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
        
        current_state = next_state

    return env