import os
import time
import threading
import random
import numpy as np
import tensorflow as tf


from tensorflow.keras.layers import Conv2D, Flatten, Dense, concatenate
from tensorflow.keras.initializers import RandomUniform
from tensorflow_probability import distributions as tfd

import ali_env
from library.logging_pack import *

# 멀티쓰레딩을 위한 글로벌 변수
global episode, score_avg, score_max
episode, score_avg, score_max = 0, 0, -100
num_episode = 8000000

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
class A3CAgent():
    def __init__(self):
        # 상태와 행동의 크기 정의
        # self.state_size = (84, 84, 4)
        # A3C 하이퍼파라미터
        self.discount_factor = 0.99
        self.no_op_steps = 30
        self.lr = 1e-4
        # 쓰레드의 갯수
        self.threads = 6

        # 글로벌 인공신경망 생성
        self.global_model = ActorCritic()
        # 글로벌 인공신경망의 가중치 초기화
        self.global_model.build([tf.TensorShape((None, 123, 5, 1)),
                                 tf.TensorShape((None, 962)),
                                 tf.TensorShape((None, 5))])

        # 글로벌 인공신경망 저장된 모델부터 학습 시작
        model_path = './save_model/model'
        self.global_model.load_weights(model_path)



        # 인공신경망 업데이트하는 옵티마이저 함수 생성
        self.optimizer = tf.compat.v1.train.AdamOptimizer(self.lr, use_locking=True)

        # 텐서보드 설정
        self.writer = tf.summary.create_file_writer('summary/ali_a3c')
        # 학습된 글로벌신경망 모델을 저장할 경로 설정
        self.model_path = os.path.join(os.getcwd(), 'save_model', 'model')

    # 쓰레드를 만들어 학습을 하는 함수
    def train(self):
        # 쓰레드 수 만큼 Runner 클래스 생성
        runners = [Runner(self.global_model, self.optimizer,
                          self.discount_factor,
                          self.writer) for i in range(self.threads)]

        # 각 쓰레드 시정
        for i, runner in enumerate(runners):
            print("Start worker #{:d}".format(i))
            runner.start()

        # 10분 (600초)에 한 번씩 모델을 저장
        while True:
            self.global_model.save_weights(self.model_path, save_format="tf")
            time.sleep(60 * 10)

# 액터러너 클래스 (쓰레드)
class Runner(threading.Thread):
    global_episode = 0

    def __init__(self, global_model,
                 optimizer, discount_factor, writer):
        threading.Thread.__init__(self)

        # A3CAgent 클래스에서 넘겨준 하이준 파라미터 설정
        # self.action_size = action_size
        # self.state_size = state_size
        self.global_model = global_model
        self.optimizer = optimizer
        self.discount_factor = discount_factor

        self.states, self.actions, self.rewards = [], [], []

        # 환경, 로컬신경망, 텐서보드 생성
        self.local_model = ActorCritic()
        self.env = ali_env.Ali_Environment()
        self.writer = writer

        # 학습 정보를 기록할 변수
        self.avg_p_max = 0
        self.avg_loss = 0
        # k-타임스텝 값 설정
        self.t_max = 20
        self.t = 0
        # 불필요한 행동을 줄여주기 위한 dictionary
        # self.action_dict = {0:1, 1:2, 2:3, 3:3}

    # 텐서보드에 학습 정보를 기록
    def draw_tensorboard(self, score, step, e):
        avg_p_max = self.avg_p_max / float(step)
        with self.writer.as_default():
            tf.summary.scalar('Score/Episode', score, step=e)
            tf.summary.scalar('Sigma/Episode', avg_p_max, step=e)
            tf.summary.scalar('Duration/Episode', step, step=e)

    # # 정책신경망의 출력을 받아 확률적으로 행동을 선택
    # def get_action(self, history):
    #     history = np.float32(history / 255.)
    #     policy = self.local_model(history)[0][0]
    #     policy = tf.nn.softmax(policy)
    #     action_index = np.random.choice(self.action_size, 1, p=policy.numpy())[0]
    #     return action_index, policy

    # 정책신경망의 출력을 받아 확률적으로 행동을 선택
    def get_action(self, state):
        # logger.debug("get_action!! current_i : " + str(self.env.current_i))
        mu, sigma, _ = self.local_model(state)
        dist = tfd.Normal(loc=mu[0], scale=sigma[0])
        action = dist.sample([1])[0]
        action = np.clip(action, 0, 1)
        # logger.debug("mu, sigma, action : " + str((mu, sigma, action)))
        return action, sigma

    # 샘플을 저장
    def append_sample(self, state, action, reward):
        self.states.append(state)
        # act = np.zeros(1)
        # act[action] = 1
        # act = action
        self.actions.append(action)
        self.rewards.append(reward)

    # k-타임스텝의 prediction 계산
    def discounted_prediction(self, rewards, done):
        # logger.debug("discounted_prediction!!!")
        discounted_prediction = np.zeros_like(rewards)
        running_add = 0

        if not done:
            # value function
            last_state = self.states[-1]
            running_add = self.local_model(last_state)[-1][0].numpy()
            # logger.debug("running_add : " + str(running_add))

        for t in reversed(range(0, len(rewards))):
            running_add = running_add * self.discount_factor + rewards[t]
            discounted_prediction[t] = running_add
        return discounted_prediction

    # 저장된 샘플들로 A3C의 오류함수를 계산
    def compute_loss(self, done):
        # logger.debug("compute_loss!!!")

        discounted_prediction = self.discounted_prediction(self.rewards, done)
        discounted_prediction = tf.convert_to_tensor(discounted_prediction[:, None],
                                                     dtype=tf.float32)

        # states = np.zeros((len(self.states), 84, 84, 4))
        #
        # for i in range(len(self.states)):
        #     states[i] = self.states[i]
        # states = np.float32(states / 255.)

        input_day_list = []
        input_sec_list = []
        input_jango_list = []
        for tup in self.states:
            input_day_list.append(tup[0])
            input_sec_list.append(tup[1])
            input_jango_list.append(tup[2])

        input_day_concat = np.concatenate(input_day_list, axis=0)
        input_sec_concat = np.concatenate(input_sec_list, axis=0)
        input_jango_concat = np.concatenate(input_jango_list, axis=0)
        states = (input_day_concat, input_sec_concat, input_jango_concat)

        # states : 스택쌓기!!
        mus, sigmas, values = self.local_model(states)
        # logger.debug("mus, sigmas, values : " + str((mus, sigmas, values)))

        # 가치 신경망 업데이트
        advantages = discounted_prediction - values
        critic_loss = 0.5 * tf.reduce_sum(tf.square(advantages))

        # 정책 신경망 업데이트
        action = tf.convert_to_tensor(self.actions, dtype=tf.float32)
        # logger.debug("action : " + str(action))
        dists = tfd.Normal(loc=mus, scale=sigmas)
        # logger.debug("dists : " + str(dists))
        action_probs = dists.prob(action)
        # logger.debug("action_probs : " + str(action_probs))
        cross_entropy = -tf.math.log(action_probs + 1e-5)
        actor_loss = tf.reduce_sum(cross_entropy * tf.stop_gradient(advantages))

        total_loss = 0.5 * critic_loss + actor_loss

        return total_loss

    # 로컬신경망을 통해 그레이디언트를 계산하고, 글로벌 신경망을 계산된 그레이디언트로 업데이트
    def train_model(self, done):
        # logger.debug("train_model!!!")
        global_params = self.global_model.trainable_variables
        local_params = self.local_model.trainable_variables


        with tf.GradientTape() as tape:
            total_loss = self.compute_loss(done)

        # 로컬신경망의 그레이디언트 계산
        grads = tape.gradient(total_loss, local_params)
        # 안정적인 학습을 위한 그레이디언트 클리핑
        grads, _ = tf.clip_by_global_norm(grads, 40.0)
        # 로컬신경망의 오류함수를 줄이는 방향으로 글로벌신경망을 업데이트
        # logger.debug(str((grads, global_params)))
        # logger.debug("global_params : " + str(global_params))
        # logger.debug("local_params : " + str(local_params))
        self.optimizer.apply_gradients(zip(grads, global_params))
        # 로컬신경망의 가중치를 글로벌신경망의 가중치로 업데이트
        self.local_model.set_weights(self.global_model.get_weights())
        # 업데이트 후 저장된 샘플 초기화
        self.states, self.actions, self.rewards = [], [], []


    def run(self):
        # 액터러너끼리 공유해야하는 글로벌 변수
        global episode, score_avg, score_max

        step = 0
        while episode < num_episode:
            done = False

            score = 0
            observe = self.env.reset()
            done = self.env.done

            # 프레임을 전처리 한 후 4개의 상태를 쌓아서 입력값으로 사용.
            # state = pre_processing(observe)
            state = observe

            while not done:
                step += 1
                self.t += 1

                # 정책 확률에 따라 행동을 선택
                action, sigma = self.get_action(state)

                # 선택한 행동으로 환경에서 한 타임스텝 진행
                observe, reward, done, final_score = self.env.step(action)

                # 각 타임스텝마다 상태 전처리
                # next_state = pre_processing(observe)
                next_state = observe

                # 정책확률의 최대값
                self.avg_p_max += np.amin(sigma.numpy())

                # score += reward
                # reward = np.clip(reward, -1., 1.)

                # 샘플을 저장
                self.append_sample(state, action, reward)

                state = next_state

                # 에피소드가 끝나거나 최대 타임스텝 수에 도달하면 학습을 진행
                if self.t >= self.t_max or done:
                    self.train_model(done)
                    self.t = 0

                if done:
                    # 각 에피소드 당 학습 정보를 기록
                    episode += 1
                    score = final_score
                    score_max = score if score > score_max else score_max
                    score_avg = 0.9 * score_avg + 0.1 * score if score_avg != 0 else score

                    log = "episode: {:5d} | score : {:4.1f} | ".format(episode, score)
                    log += "score max : {:4.1f} | ".format(score_max)
                    log += "score avg : {:.3f}".format(score_avg)
                    print(log)

                    self.draw_tensorboard(score, step, episode)

                    self.avg_p_max = 0
                    step = 0


if __name__ == "__main__":
    global_agent = A3CAgent()
    global_agent.train()