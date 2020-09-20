from library.logging_pack import *
from sqlalchemy import create_engine, event
from library import cf
import re
import datetime
from datetime import datetime
from datetime import timedelta
import pandas as pd
import numpy as np
from agent import *
import time
import itertools

import pymysql
pymysql.install_as_MySQLdb()

def escape_percentage(conn, clauseelement, multiparams, params):
    # execute로 실행한 sql문이 들어왔을 때 %를 %%로 replace
    if isinstance(clauseelement, str) and '%' in clauseelement and multiparams is not None:
        while True:
            replaced = re.sub(r'([^%])%([^%s])', r'\1%%\2', clauseelement)
            if replaced == clauseelement:
                break
            clauseelement = replaced

    return clauseelement, multiparams, params




class Ali_Environment():
    def __init__(self):
        self.variable_setting()
        self.db_name_setting()
        self.candidate_universe_init()


    # region Environment init setting
    def variable_setting(self):
        self.date_list = ["20200824", "20200825", "20200826", "20200827", "20200828",
                          "20200831", "20200901", "20200902", "20200903", "20200904",
                          "20200907", "20200908", "20200909", "20200910", "20200911",
                          "20200914", "20200915", "20200916", "20200917"]
        self.last_date_list = ["20200821",
                               "20200824", "20200825", "20200826", "20200827", "20200828",
                               "20200831", "20200901", "20200902", "20200903", "20200904",
                               "20200907", "20200908", "20200909", "20200910", "20200911",
                               "20200914", "20200915", "20200916"]

        start_time_str = "20200918" + "090000"
        start_time = datetime.strptime(start_time_str, "%Y%m%d%H%M%S")
        self.time_stamp_list = []
        for i in range(481):
            self.time_stamp_list.append(datetime.strftime(start_time + timedelta(0, 5 * i), "%Y%m%d%H%M%S")[-6:])

        # np.random.seed(42)

    def db_name_setting(self):
        self.engine_universe_new_rocket = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/universe_new_rocket",
            encoding='utf-8')
        self.engine_daily_buy_list = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/daily_buy_list",
            encoding='utf-8')
        self.engine_daily_craw = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/daily_craw",
            encoding='utf-8')
        event.listen(self.engine_universe_new_rocket, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_daily_buy_list, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_daily_craw, 'before_execute', escape_percentage, retval=True)

    def candidate_universe_init(self):
        self.candidate_universe_list = []
        for date in self.date_list:
            sql = "select date, code from `" + date + "_setting_data" + "`"
            temp_list = self.engine_universe_new_rocket.execute(sql).fetchall()
            for tup in temp_list:
                self.candidate_universe_list.append('_'.join(tup))

    # code명으로 code_name을 가져오는 함수
    def get_name_by_code(self, code):
        sql = "select code_name from stock_item_all where code = '%s'"
        code_name = self.engine_daily_buy_list.execute(sql % (code)).fetchall()
        # print(code_name)
        if code_name:
            return code_name[0][0]
        else:
            return False
    # endregion Environment init setting

    def reset(self):
        # logger.debug("environment reset!!")
        self.done = False
        # 데이터 하나 랜덤 추출
        universe_name = self.candidate_universe_list[np.random.choice(len(self.candidate_universe_list), 1)[0]]
        date, code = universe_name.split('_')
        code_name = self.get_name_by_code(code)
        # logger.debug("train with " + str(universe_name) + "!!!")

        # 일봉 데이터 세팅
        sql = "select open, high, low, close, volume from `" + code_name + "` where date < " + date + " order by date desc limit 123"
        temp_data = self.engine_daily_craw.execute(sql).fetchall()

        self.df_day_data = pd.DataFrame(temp_data, columns=['open', 'high', 'low', 'close', 'volume'])
        # self.df_day_data.drop(['index'], axis=1, inplace=True)
        self.last_close = self.df_day_data.iloc[0, 3]
        self.mean_volume = self.df_day_data.mean()['volume']

        self.df_day_data[self.df_day_data.columns[:4]] /= self.last_close
        self.df_day_data[self.df_day_data.columns[-1]] /= self.mean_volume

        # 초봉 데이터 세팅
        sql = "select time, price, volume from `" + universe_name + "`"
        temp_data = self.engine_universe_new_rocket.execute(sql).fetchall()

        df_data = pd.DataFrame(temp_data, columns=['time', 'price', 'volume'])
        # df_data.drop(['index'], axis=1, inplace=True)
        df_data['time'] = df_data['time'].apply(lambda x: x[-6:])
        df_data.set_index(['time'], inplace=True)

        self.df_sec_data = pd.DataFrame(index=self.time_stamp_list, columns=df_data.columns)
        for idx, row in df_data.iterrows():
            self.df_sec_data.loc[idx] = row
        for i, tup in enumerate(self.df_sec_data.iterrows()):
            if tup[0] not in df_data.index:
                if i != 0:
                    self.df_sec_data.iloc[i] = self.df_sec_data.iloc[i - 1]
        self.df_sec_data.fillna(0, inplace=True)

        # logger.debug("df_sec_data")
        # logger.debug("df_sec_data_length : " + str(len(self.df_sec_data)))

        self.df_sec_data['price'] /= self.last_close

        # 시작 포인트 잡기
        for i, tup in enumerate(self.df_sec_data.iterrows()):
            if tup[1]['price'] >= 1.02 and tup[1]['volume'] >= 500000:
                self.current_i = i
                self.start_index = tup[0]
                self.current_price = tup[1]['price']
                # logger.debug(self.current_i)
                break
            # logger.debug(str(i))
        if self.current_i == 480:
            self.done = True

        self.df_sec_data['volume'] /= self.mean_volume

        # 잔고 데이터 세팅
        self.avg_price = 0
        self.current_holding_ratio = 0
        self.valuation_profit = 0
        self.realized_profit = 0

        # 인공신경망 input 형태로 바꿔줌
        input_day = np.zeros((123, 5))
        input_day[:len(self.df_day_data), :] = self.df_day_data.values
        input_day = input_day.reshape((1, 123, 5, 1))
        input_day = input_day.astype('float32')
        input_sec = np.zeros_like(self.df_sec_data)
        input_sec[:self.current_i+1, :] = self.df_sec_data.iloc[:self.current_i+1, :]
        input_sec = input_sec.flatten()
        input_sec = input_sec.reshape((1, len(input_sec)))
        input_sec = input_sec.astype('float32')
        input_jango = np.array([self.current_i / 480, self.avg_price, self.current_holding_ratio, self.valuation_profit, self.realized_profit])
        input_jango = input_jango.reshape((1, len(input_jango)))
        input_jango = input_jango.astype('float32')


        return (input_day, input_sec, input_jango)

    def step(self, action):
        # logger.debug("environment step!!! current_i : " + str(self.current_i))
        self.current_price = self.df_sec_data.iloc[self.current_i]['price']
        next_holding_ratio = action[0]
        action_amount = next_holding_ratio - self.current_holding_ratio
        # action_amount > 0 이면 매수 진행
        if action_amount > 0:
            # logger.debug("(self.avg_price, self.current_price) : " + str((self.avg_price, self.current_price)))
            # logger.debug("(self.current_holding_ratio, action_amount) : " + str((self.current_holding_ratio, action_amount)) )
            self.avg_price = np.average((self.avg_price, self.current_price), weights=(self.current_holding_ratio, action_amount))
            # logger.debug("매수!!!! avg_price : " + str(self.avg_price))
        # action_amount < 0 이면 매도 진행
        elif action_amount < 0:
            self.realized_profit += (self.current_price * 0.9972 / self.avg_price - 1) * 100 * np.abs(action_amount)
            # logger.debug("매도!!!! realized_profit : " + str(self.realized_profit))

        self.current_i += 1
        self.current_holding_ratio = next_holding_ratio
        if self.avg_price == 0:
            self.valuation_profit = 0
        else:
            self.valuation_profit = (self.current_price * 0.9972 / self.avg_price - 1) * 100 * self.current_holding_ratio

        reward = self.valuation_profit + self.realized_profit

        input_day = np.zeros((123, 5))
        input_day[:len(self.df_day_data), :] = self.df_day_data.values
        input_day = input_day.reshape((1, 123, 5, 1))
        input_day = input_day.astype('float32')
        input_sec = np.zeros_like(self.df_sec_data)
        input_sec[:self.current_i + 1, :] = self.df_sec_data.iloc[:self.current_i + 1, :]
        input_sec = input_sec.flatten()
        input_sec = input_sec.reshape((1, len(input_sec)))
        input_sec = input_sec.astype('float32')
        input_jango = np.array(
            [self.current_i / 480, self.avg_price, self.current_holding_ratio, self.valuation_profit, self.realized_profit])
        input_jango = input_jango.reshape((1, len(input_jango)))
        input_jango = input_jango.astype('float32')
        # logger.debug("jango!!! (current_i/480, avg_price, current_holding_ratio, val_profit, realized_profit) : " + str(input_jango))

        final_score = 0
        if self.current_i == 480:
            self.done = True
            final_score = reward

        return (input_day, input_sec, input_jango), reward, self.done, final_score























