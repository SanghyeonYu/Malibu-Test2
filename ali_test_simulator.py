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

# GPU 메모리 증가 허용
physical_devices = tf.config.list_physical_devices('GPU')
try:
  tf.config.experimental.set_memory_growth(physical_devices[0], True)
except:
  # Invalid device or cannot modify virtual devices once initialized.
  pass


# ActorCritic 인공신경망
class ActorCritic(tf.keras.Model):
    def __init__(self):
        super(ActorCritic, self).__init__()
        self.day_layers = [
            Conv2D(filters=32, kernel_size=(5, 5), strides=2, padding='valid', activation='relu',
                   input_shape=[1, 123, 5, 1]),
            Conv2D(filters=16, kernel_size=(4, 1), strides=2, padding='valid', activation='relu'),
            Conv2D(filters=8, kernel_size=(3, 1), strides=2, padding='valid', activation='relu'),
            Flatten()
        ]
        self.sec_layers = [
            Dense(967, activation='relu'),
            Dense(480, activation='relu'),
            Dense(120, activation='relu')
        ]
        self.shared_fc = Dense(120, activation='relu')

        self.actor_mu = Dense(1, kernel_initializer=RandomUniform(-1e-3, 1e-3))
        self.actor_sigma = Dense(1, activation='sigmoid',
                                 kernel_initializer=RandomUniform(-1e-3, 1e-3))
        self.critic_out = Dense(1, activation='linear')

    def call(self, inputs):
        # logger.debug("actor_critic.call!!!")
        input_day, input_sec, input_jango = inputs
        # logger.debug("input_shape : " + str((input_day.shape, input_sec.shape, input_jango.shape)))
        for layer in self.day_layers:
            input_day = layer(input_day)

        input_sec = concatenate([input_sec, input_jango])
        for layer in self.sec_layers:
            input_sec = layer(input_sec)

        concat = concatenate([input_day, input_sec, input_jango])
        concat = self.shared_fc(concat)

        mu = self.actor_mu(concat)
        sigma = self.actor_sigma(concat)
        sigma += 1e-5
        sigma *= 0.2

        value = self.critic_out(concat)

        # logger.debug("mu, sigma, value : " + str((mu, sigma, value)))
        return mu, sigma, value


# A3CAgent 클래스 (글로벌신경망)
class A3CTestAgent():
    def __init__(self, model_path):
        # 글로벌 인공신경망 생성
        self.model = ActorCritic()
        # 글로벌 인공신경망의 가중치 초기화
        # self.global_model.build([tf.TensorShape((None, 123, 5, 1)),
        #                          tf.TensorShape((None, 962)),
        #                          tf.TensorShape((None, 5))])

        self.model.load_weights(model_path)

    # 정책신경망의 출력을 받아 확률적으로 행동을 선택
    def get_action(self, state):
        # logger.debug("get_action!! current_i : " + str(self.env.current_i))
        mu, sigma, value = self.model(state)
        dist = tfd.Normal(loc=mu[0], scale=sigma[0])
        action = dist.sample([1])[0]
        action = np.clip(action, 0, 1)
        # logger.debug("mu, sigma, action : " + str((mu, sigma, action)))
        return action, sigma, value


if __name__ == "__main__":
    # 테스트를 위한 환경, 모델 생성
    env = ali_env.Ali_Environment()

    model_path = './save_model - 202009202306/model'
    agent = A3CTestAgent(model_path)

    df_total_summary = pd.DataFrame(columns=['name', 'final_profit'])
    path_log = './ali_test_log2/'

    num_episode = len(env.candidate_universe_list)
    for e in range(num_episode):
        done = False

        score = 0
        observe = env.reset(e)
        state = observe
        done = env.done

        df_log = pd.DataFrame(columns=['time', 'price', 'value', 'action', 'avg_price', 'v_profit', 'r_profit'],
                              index=env.df_sec_data.index)
        df_log['price'] = env.df_sec_data['price']
        df_log.reset_index(inplace=True)
        df_log['time'] = env.df_sec_data.index


        while not done:

            # 정책 확률에 따라 행동을 선택
            action, sigma, value = agent.get_action(state)
            df_log['price'][env.current_i] = env.current_price
            df_log['value'][env.current_i] = value.numpy()[0][0]
            df_log['action'][env.current_i] = action[0]
            df_log['avg_price'][env.current_i] = env.avg_price
            df_log['v_profit'][env.current_i] = env.valuation_profit
            df_log['r_profit'][env.current_i] = env.realized_profit

            # 선택한 행동으로 환경에서 한 타임스텝 진행
            observe, reward, done, final_score = env.step(action)

            # 각 타임스텝마다 상태 전처리
            # next_state = pre_processing(observe)
            next_state = observe
            state = next_state

            if done:
                # 각 에피소드 당 학습 정보를 기록
                score = final_score

                log = "episode: {} | score : {:4.1f} | ".format(env.universe_name, score)

                df_log.fillna(0, inplace=True)


                path = path_log + env.universe_name + '.csv'
                df_log.to_csv(path_or_buf=path)
                df_log.to_sql(env.universe_name, env.engine_simulator_ali, if_exists='replace')
                print(log)

                temp_dict = {'name': env.universe_name, 'final_profit': score}
                df_total_summary = df_total_summary.append(temp_dict, ignore_index=True)
    path = path_log + 'ali_test_total_summary.csv'
    df_total_summary.to_csv(path_or_buf=path)




