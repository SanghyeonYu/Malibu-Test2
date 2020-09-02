
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

class Simulator():
    def __init__(self):
        # variable setting
        self.db_name_setting()
        self.variable_setting()
        self.get_universe_list()

        # simulating 기록 Table 초기화

        pass
# region setting
    # db 세팅 함수
    def db_name_setting(self):
        self.engine_universe_rocket = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/universe_rocket",
            encoding='utf-8')
        self.engine_simulator_rocket = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/simulator_rocket",
            encoding='utf-8')
        event.listen(self.engine_universe_rocket, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_simulator_rocket, 'before_execute', escape_percentage, retval=True)

    def variable_setting(self):
        self.date = "20200901"

        self.invest_unit = 200000

        self.consider_len = 20
        self.algorithm_sell_num = 2
        self.algorithm_buy_num = 2

        self.agent = Agent()

    def get_universe_list(self):
        logger.debug("get_universe_list")
        sql = "select code from " + self.date + "_setting_data"
        temp_list = self.engine_universe_rocket.execute(sql).fetchall()
        self.universe_list = [x[0] for x in temp_list]

# endregion setting

# region DB Control
    def get_one_code_data(self, code):
        sql = "select * from " + self.date + "_" + code
        data = self.engine_universe_rocket.execute(sql).fetchall()
        df_data = pd.DataFrame(data, columns=['index', 'time', 'code', 'price', 'volume',
                                               'hoga_sell_amount', 'hoga_buy_amount'])
        return df_data

    def get_one_code_data_to_csv(self, code):
        df_data = self.get_one_code_data(code)
        path = code +".csv"
        print(df_data)
        df_data.to_csv(path_or_buf=path)

    def init_result_table(self, table_name):
        logger.debug("init_result_table !! ")

        #  추가하면 여기에도 추가해야함
        result_dict = {'consider_len': [],
                       'end_time': [],
                       'buy_discount_rate': [],
                       'sell_discount_rate': [],
                       'buy_power_threshold': [],
                       'sell_power_threshold': [],
                       'buy_accel_threshold': [],
                       'sell_accel_threshold': [],
                       'buy_power_ratio_threshold': [],
                       'mean_earning_rate': [],
                       'total_trade_count': [],
                       'oscillation_count': [],
                       'oscillation_ratio': []}
        df_setting_data = pd.DataFrame(result_dict,
                                    columns=['consider_len',
                                               'end_time',
                                               'buy_discount_rate',
                                               'sell_discount_rate',
                                               'buy_power_threshold',
                                               'sell_power_threshold',
                                               'buy_accel_threshold',
                                               'sell_accel_threshold',
                                               'buy_power_ratio_threshold',
                                               'mean_earning_rate',
                                               'total_trade_count',
                                               'oscillation_count',
                                               'oscillation_ratio'])
        # 자료형
        df_setting_data.loc[0, 'consider_len'] = int(0)
        df_setting_data.loc[0, 'end_time'] = int(0)
        df_setting_data.loc[0, 'buy_discount_rate'] = float(0)
        df_setting_data.loc[0, 'sell_discount_rate'] = float(0)
        df_setting_data.loc[0, 'buy_power_threshold'] = float(0)
        df_setting_data.loc[0, 'sell_power_threshold'] = float(0)
        df_setting_data.loc[0, 'buy_accel_threshold'] = float(0)
        df_setting_data.loc[0, 'sell_accel_threshold'] = float(0)
        df_setting_data.loc[0, 'buy_power_ratio_threshold'] = float(0)
        df_setting_data.loc[0, 'mean_earning_rate'] = float(0)
        df_setting_data.loc[0, 'total_trade_count'] = int(0)
        df_setting_data.loc[0, 'oscillation_count'] = int(0)
        df_setting_data.loc[0, 'oscillation_ratio'] = float(0)

        df_setting_data.to_sql(table_name, self.engine_simulator_rocket, if_exists='replace')

# endregion DB Control

    def run(self):
        # 전체 시뮬레이션 요약 결과 저장 테이블 만들기
        # self.init_result_table("result_summary")


        # 시뮬레이션 조건별 이터레이션
        consider_len_list = [20]
        buy_discount_rate_list = [0.5, 0.7]
        sell_discount_rate_list = [0.5, 0.7, 0.9]
        buy_power_threshold_list = [2, 5, 10, 100]
        sell_power_threshold_list = [1, 2]
        buy_accel_threshold_list = [0.3, 0.5]
        sell_accel_threshold_list = [0.3, 0.5, 0.7]
        buy_power_ratio_threshold_list = [100, 2000, 20000]
        end_time_list = [20200901091000, 20200901092000, 20200901093000, 20200901101000]
        simulation_count = 0
        for consider_len in consider_len_list:
            for buy_discount_rate in buy_discount_rate_list:
                for sell_discount_rate in sell_discount_rate_list:
                    for buy_power_threshold in buy_power_threshold_list:
                        for sell_power_threshold in sell_power_threshold_list:
                            for buy_accel_threshold in buy_accel_threshold_list:
                                for sell_accel_threshold in sell_accel_threshold_list:
                                    for buy_power_ratio_threshold in buy_power_ratio_threshold_list:
                                        # 시뮬레이션 조건에 맞는 table 생성
                                        # 시뮬레이션 결과를 기록할 DataFrame 생성
                                        # record_name = "record_" + str(consider_len) + "_" +\
                                        #               str(buy_discount_rate) + "_" + str(sell_discount_rate) + "_" +\
                                        #               str(buy_power_threshold) + "_" + str(sell_power_threshold) + "_" +\
                                        #               str(buy_accel_threshold) + "_" + str(sell_accel_threshold) + "_" +\
                                        #               str(buy_power_ratio_threshold)
                                        record_name = "record_" + self.date + "_b_" + str(simulation_count)
                                        df_record = pd.DataFrame(columns=['trade_index', 'code', 'buy_time', 'sell_time', 'buy_price', 'sell_price',
                                                                          'amount', 'profit', 'earning_rate'])

                                        # 종목별 이터레이션
                                        temptime = time.time()
                                        trade_index = 0
                                        for code in self.universe_list:
                                            # state 생성
                                            state = State(code, code)
                                            possessed = False
                                            # universe_rocket db에서 데이터 가져옴
                                            data = self.get_one_code_data(code)
                                            # time step 이터레이션
                                            for i, row in data.iterrows():
                                                price = np.abs(row['price'])
                                                state.update_price(price)
                                                state.update_volume(row['volume'])

                                                # 보유하고 있으면 매도 확인
                                                if possessed:
                                                    if self.agent.check_sell_condition_simulation(state, consider_len, sell_discount_rate, sell_power_threshold, sell_accel_threshold):
                                                        # 매도!!
                                                        possessed = False
                                                        state.possessed_num = 0
                                                        # DB 처리, 계좌 처리
                                                        sell_price = price
                                                        buy_price = df_record.loc[trade_index, 'buy_price']
                                                        amount = df_record.loc[trade_index, 'amount']

                                                        df_record.loc[trade_index, 'sell_time'] = row['time']
                                                        df_record.loc[trade_index, 'sell_price'] = sell_price
                                                        df_record.loc[trade_index, 'profit'] = (sell_price - buy_price) * amount
                                                        df_record.loc[trade_index, 'earning_rate'] = np.round(((sell_price - buy_price) / buy_price) * 100 - 0.28, 2)

                                                        # 매도 했으면 trade_index +1
                                                        trade_index += 1

                                                # 보유하고 있지 않으면 매수 확인
                                                if not possessed:
                                                    if self.agent.check_buy_condition_simulation(state, consider_len, buy_discount_rate, buy_power_threshold, buy_power_ratio_threshold, buy_accel_threshold):
                                                        possessed = True
                                                        buy_num = int(np.round(self.invest_unit / state.price[-1]))
                                                        state.possessed_num = buy_num
                                                        # DB 처리, 계좌 처리
                                                        temp_dict = {'trade_index': trade_index,
                                                                     'code': code,
                                                                     'buy_time': row['time'],
                                                                     'buy_price': price,
                                                                     'amount': buy_num}
                                                        df_record = df_record.append(temp_dict, ignore_index=True)
                                            # 한 종목 이터레이션 끝났는데 매도 못 했으면 trade_index +1
                                            if possessed:
                                                trade_index += 1
                                        print(str(simulation_count) + " 번째 시뮬레이션 소요 시간 : ", time.time() - temptime)
                                        simulation_count += 1

                                        # 종목별 이터레이션 끝, df_record DB에 저장
                                        df_record = df_record.fillna(0)
                                        df_record.drop(df_record[df_record['sell_price'] == 0].index, inplace=True)
                                        df_record.reset_index()
                                        if len(df_record) != 0:
                                            df_record.to_sql(record_name, self.engine_simulator_rocket, if_exists='replace')

                                        # record 요약 데이터 만들기
                                        # oscillation 개수, 비율 계산
                                        df_record['timedelta'] = (df_record['sell_time'].apply(
                                            lambda x: datetime.strptime(str(x), '%Y%m%d%H%M%S')) - df_record[
                                                                   'buy_time'].apply(
                                            lambda x: datetime.strptime(str(x), '%Y%m%d%H%M%S'))).apply(
                                            lambda x: x.seconds)

                                        for end_time in end_time_list:
                                            temp_df_record = df_record[df_record['sell_time'].apply(lambda x: int(x)) <= end_time]
                                            mean_earning_rate = np.round(np.mean(temp_df_record['earning_rate']), 2)
                                            total_trade_count = len(temp_df_record)
                                            oscillation_count = temp_df_record[(temp_df_record['timedelta'] <= 60) & (temp_df_record['earning_rate'] <= 0)].count()[0]
                                            oscillation_ratio = np.round(oscillation_count / (total_trade_count + 0.00001), 2)

                                            result_dict = {'consider_len': [consider_len],
                                                           'end_time': [end_time],
                                                           'buy_discount_rate': [buy_discount_rate],
                                                           'sell_discount_rate': [sell_discount_rate],
                                                           'buy_power_threshold': [buy_power_threshold],
                                                           'sell_power_threshold': [sell_power_threshold],
                                                           'buy_accel_threshold': [buy_accel_threshold],
                                                           'sell_accel_threshold': [sell_accel_threshold],
                                                           'buy_power_ratio_threshold': [buy_power_ratio_threshold],
                                                           'mean_earning_rate': [mean_earning_rate],
                                                           'total_trade_count': [total_trade_count],
                                                           'oscillation_count': [oscillation_count],
                                                           'oscillation_ratio': [oscillation_ratio]}
                                            df_result = pd.DataFrame(result_dict)
                                            check = len(df_result.dropna())
                                            if check != 0:
                                                df_result.to_sql("result_summary_20200901_b", self.engine_simulator_rocket,
                                                                 if_exists='append')




if __name__ == "__main__":
    simulator = Simulator()
    simulator.run()

    sql = "select * from result_summary_20200901_b"
    data = simulator.engine_simulator_rocket.execute(sql).fetchall()
    df_data = pd.DataFrame(data, columns=['index',
                                          'consider_len',
                                           'end_time',
                                           'buy_discount_rate',
                                           'sell_discount_rate',
                                           'buy_power_threshold',
                                           'sell_power_threshold',
                                           'buy_accel_threshold',
                                           'sell_accel_threshold',
                                           'buy_power_ratio_threshold',
                                           'mean_earning_rate',
                                           'total_trade_count',
                                           'oscillation_count',
                                           'oscillation_ratio'])
    path = "result_summary_20200901_b.csv"
    df_data.to_csv(path_or_buf=path)