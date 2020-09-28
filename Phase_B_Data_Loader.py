from library.logging_pack import *
import re
from library import cf
import datetime
from datetime import datetime
from datetime import timedelta

import pandas as pd
import numpy as np

import pymysql
from sqlalchemy import create_engine, event
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



class Data_Loader():
    def __init__(self):
        logger.debug("data_loader_init")
        self.variable_setting()
        self.db_name_setting()
        self.candidate_universe_init()
        # 일봉 데이터 세팅
        # code_name = '삼성전자'
        # date = '20200925'
        # sql = "select close, volume from `" + code_name + "` where date < " + date + " order by date desc limit 120"
        # temp_data = self.env.engine_daily_craw.execute(sql).fetchall()
        #
        # self.df_day_data = pd.DataFrame(temp_data, columns=['close', 'volume'])
        # # self.df_day_data.to_csv(path_or_buf='20200924_005930.csv')
        # print(self.df_day_data)

        # # 초봉 데이터 세팅
        # universe_name = '20200910_005930'
        # sql = "select time, price, volume from `" + universe_name + "`"
        # temp_data = self.env.engine_universe_new_rocket.execute(sql).fetchall()
        #
        # df_data = pd.DataFrame(temp_data, columns=['time', 'price', 'volume'])
        # df_data['time'] = df_data['time'].apply(lambda x: x[-6:])
        # df_data.set_index(['time'], inplace=True)
        # df_data.to_csv(path_or_buf='20200910_005930_universe.csv')

    # region init
    def variable_setting(self):
        self.date_list = ["20200824", "20200825", "20200826", "20200827", "20200828",
                          "20200831", "20200901", "20200902", "20200903", "20200904",
                          "20200907", "20200908", "20200909", "20200910", "20200911",
                          "20200914", "20200915", "20200916", "20200917", "20200918",
                          "20200921", "20200922", "20200923", "20200924", "20200925"]
        # self.date_list = ["20200922"]
        # self.last_date_list = ["20200821",
        #                        "20200824", "20200825", "20200826", "20200827", "20200828",
        #                        "20200831", "20200901", "20200902", "20200903", "20200904",
        #                        "20200907", "20200908", "20200909", "20200910", "20200911",
        #                        "20200914", "20200915", "20200916"]

        start_time_str = "20200918" + "090000"
        start_time = datetime.strptime(start_time_str, "%Y%m%d%H%M%S")
        self.time_stamp_list = []
        for i in range(481):
            self.time_stamp_list.append(datetime.strftime(start_time + timedelta(0, 5 * i), "%Y%m%d%H%M%S")[-6:])

        self.duration_list = [20, 40, 60, 120]

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
        self.engine_trader_ali = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/trader_ali",
            encoding='utf-8')
        self.engine_simulator_ali = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/simulator_ali",
            encoding='utf-8')
        event.listen(self.engine_universe_new_rocket, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_daily_buy_list, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_daily_craw, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_trader_ali, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_simulator_ali, 'before_execute', escape_percentage, retval=True)

    # code명으로 code_name을 가져오는 함수
    def get_name_by_code(self, code):
        sql = "select code_name from stock_item_all where code = '%s'"
        code_name = self.engine_daily_buy_list.execute(sql % (code)).fetchall()
        # print(code_name)
        if code_name:
            return code_name[0][0]
        else:
            return False

    def candidate_universe_init(self):
        self.candidate_universe_list = []
        for date in self.date_list:
            sql = "select date, code from `" + date + "_setting_data" + "`"
            temp_list = self.engine_universe_new_rocket.execute(sql).fetchall()
            for tup in temp_list:
                self.candidate_universe_list.append('_'.join(tup))

    # endregion

    def get_volume_profile(self, df, duration):
        df_temp = df[:duration].copy()

        df_temp['volume'] /= duration
        df_temp['close_cut'] = pd.cut(df_temp['close'], bins=10).apply(lambda x: x.mid)
        volume_profile = df_temp.groupby(by=['close_cut']).sum()['volume']
        np_volume_profile = np.zeros((10, 2))
        np_volume_profile[:, 0] = volume_profile.index.values
        np_volume_profile[:, 1] = volume_profile.values
        return np_volume_profile

    def set_day_data(self, date, code):
        # 일봉 데이터 세팅
        # logger.debug("set_day_data, universe : " + str(date) + '_' + str(code))
        code_name = self.get_name_by_code(code)
        sql = "select close, volume from `" + code_name + "` where date < " + date + " order by date desc limit 120"
        temp_data = self.engine_daily_craw.execute(sql).fetchall()

        self.df_day_data = pd.DataFrame(temp_data, columns=['close', 'volume'])
        # self.df_day_data.drop(['index'], axis=1, inplace=True)
        self.last_close = self.df_day_data['close'][0]
        # logger.debug("last_close : " + str(self.last_close))
        self.mean_volume = self.df_day_data.mean()['volume']

        self.df_day_data['close'] /= self.last_close
        self.df_day_data['volume'] /= self.mean_volume
        # return self.df_day_data

    def set_sec_data(self, universe_name):
        # 초봉 데이터 세팅
        # self.universe_name = universe_name
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

        # volume을 누적이 아닌 발생량으로 계산, len : 481 -> 480이 됨
        self.df_sec_data['volume'] = self.df_sec_data['volume'] - self.df_sec_data['volume'].shift(1)
        self.df_sec_data.dropna(inplace=True)

        self.df_sec_data['price'] /= self.last_close
        self.df_sec_data['volume'] /= self.mean_volume

        # return self.df_sec_data

    def get_label_from_sec_data(self):
        self.df_label = pd.DataFrame(index=self.df_sec_data.index)
        self.df_label['label_1'] = self.df_sec_data['price'].shift(-12) / self.df_sec_data['price']
        self.df_label['label_3'] = self.df_sec_data['price'].shift(-36) / self.df_sec_data['price']
        self.df_label['label_5'] = self.df_sec_data['price'].shift(-60) / self.df_sec_data['price']
        self.df_label.replace(np.inf, 0, inplace=True)
        self.df_label.fillna(0, inplace=True)
        self.np_label = (self.df_label[:420].values >= 1.03)
        # logger.debug("greater than 1.03 ratio : " + str(self.np_label.sum() / (420*3)))

    # def get_stacked_volume_profile(self):
    #     # logger.debug("get_stacked_volume_profile")
    #     np_stacked_volume_profile_list = []
    #     for universe_name in self.candidate_universe_list:
    #         date, code = universe_name.split('_')
    #         self.set_day_data(date, code)
    #         np_volume_profile = np.ndarray((0, 2))
    #         for duration in self.duration_list:
    #             np_volume_profile = np.concatenate((np_volume_profile, self.get_volume_profile(self.df_day_data, duration)))
    #         np_stacked_volume_profile_list.append(np_volume_profile)
    #     np_stacked_volume_profile = np.stack(np_stacked_volume_profile_list)
    #     return np_stacked_volume_profile

    # def get_stacked_sec_data_and_label(self):
    #     # logger.debug("get_stacked_sec_data_and_label")
    #     np_stacked_sec_data_list = []
    #     np_stacked_label_list = []
    #     for universe_name in self.candidate_universe_list:
    #         self.set_sec_data(universe_name)
    #         np_stacked_sec_data_list.append(self.df_sec_data.values)
    #         self.get_label_from_sec_data()
    #         np_stacked_label_list.append(self.df_label.values)
    #     np_stacked_sec_data = np.stack(np_stacked_sec_data_list)
    #     np_stacked_label = np.stack(np_stacked_label_list)
    #     return np_stacked_sec_data, np_stacked_label

    def get_stacked_dataset(self):
        np_stacked_volume_profile_list = []
        np_stacked_sec_data_list = []
        np_stacked_label_list = []
        for universe_name in self.candidate_universe_list:
            # 매물대 계산
            date, code = universe_name.split('_')
            self.set_day_data(date, code)
            np_volume_profile = np.ndarray((0, 2))
            for duration in self.duration_list:
                np_volume_profile = np.concatenate(
                    (np_volume_profile, self.get_volume_profile(self.df_day_data, duration)))
            np_stacked_volume_profile_list.append(np_volume_profile)

            # 초봉 데이터 세팅
            self.set_sec_data(universe_name)
            np_stacked_sec_data_list.append(self.df_sec_data.values)

            # 라벨 계산
            self.get_label_from_sec_data()
            np_stacked_label_list.append(self.np_label)

        np_stacked_volume_profile = np.stack(np_stacked_volume_profile_list)
        np_stacked_sec_data = np.stack(np_stacked_sec_data_list)
        np_stacked_label = np.stack(np_stacked_label_list)
        return np_stacked_volume_profile, np_stacked_sec_data, np_stacked_label








if __name__ == "__main__":
    pass