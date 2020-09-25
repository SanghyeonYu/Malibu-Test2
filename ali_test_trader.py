import os
import time
import threading
import random
import numpy as np
import pandas as pd
import tensorflow as tf


from tensorflow.keras.layers import Conv2D, Flatten, Dense, concatenate
from tensorflow.keras.initializers import RandomUniform
from tensorflow_probability import distributions as tfd

import ali_env
from library.logging_pack import *

class TestTrader():
    def __init__(self):
        pass

    def get_action(self, universe_name, timestamp):
        sql = "select action, value from `" + universe_name + "` where time = " + str(timestamp)
        temp = env.engine_simulator_ali.execute(sql).fetchall()
        action = temp[0][0]
        value = temp[0][1]
        return action, value

    def run(self):
        pass

if __name__ == "__main__":
    # 테스트를 위한 환경, 모델 생성
    env = ali_env.Ali_Environment()

    agent = TestTrader()

    df_total_summary = pd.DataFrame(columns=['name', 'final_profit'])
    path_log = './ali_test_trade_log2/'

    num_episode = len(env.candidate_universe_list)
    for e in range(num_episode):
        done = False

        score = 0
        observe = env.reset(e)
        state = observe
        done = env.done
        start = False

        df_log = pd.DataFrame(columns=['time', 'price', 'value', 'action', 'avg_price', 'v_profit', 'r_profit'])
        df_log['time'] = env.df_sec_data.index

        while not done:

            # 정책 확률에 따라 행동을 선택
            action, value = agent.get_action(env.universe_name, df_log.iloc[env.current_i]['time'])
            if start == False and value >= 200:
                start = True
            if start == False:
                action = 0
            df_log['price'][env.current_i] = env.current_price
            df_log['value'][env.current_i] = value
            df_log['action'][env.current_i] = action
            df_log['avg_price'][env.current_i] = env.avg_price
            df_log['v_profit'][env.current_i] = env.valuation_profit
            df_log['r_profit'][env.current_i] = env.realized_profit

            # 선택한 행동으로 환경에서 한 타임스텝 진행
            observe, reward, done, final_score = env.step([action])

            if done:
                # 각 에피소드 당 학습 정보를 기록
                score = final_score

                log = "episode: {} | score : {:4.1f} | ".format(env.universe_name, score)

                df_log.fillna(0, inplace=True)

                path = path_log + env.universe_name + '.csv'
                df_log.to_csv(path_or_buf=path)
                df_log.to_sql(env.universe_name, env.engine_trader_ali, if_exists='replace')
                print(log)

                temp_dict = {'name': env.universe_name, 'final_profit': score}
                df_total_summary = df_total_summary.append(temp_dict, ignore_index=True)
    path = path_log + 'ali_test_trade_total_summary.csv'
    df_total_summary.to_csv(path_or_buf=path)



