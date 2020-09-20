
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

class Simulator():
    def __init__(self):
        # variable setting
        self.db_name_setting()
        self.variable_setting()

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
        self.engine_tick_craw = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/tick_craw",
            encoding='utf-8')
        self.engine_universe_new_rocket = create_engine(
            "mysql+mysqldb://" + cf.db_id + ":" + cf.db_passwd + "@" + cf.db_ip + ":" + cf.db_port + "/universe_new_rocket",
            encoding='utf-8')

        event.listen(self.engine_universe_rocket, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_simulator_rocket, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_tick_craw, 'before_execute', escape_percentage, retval=True)
        event.listen(self.engine_universe_new_rocket, 'before_execute', escape_percentage, retval=True)

    def variable_setting(self):
        self.algorithm_set_name = "alex_b_0"
        self.algorithm_set = {'consider_len_list': [20, 30],
                              'buy_discount_rate_list': [0.33, 0.4, 0.5],
                              'sell_discount_rate_list': [0.6, 0.7, 0.8],
                              'buy_power_threshold_list': [5, 10],
                              'sell_power_threshold_list': [1],
                              'buy_accel_threshold_list': [0.33, 0.5],
                              'sell_accel_threshold_list': [0.7],
                              'buy_power_ratio_threshold_list': [100, 1000, 10000, 20000],
                              'over_open_price': [True]}
        self.param_list = list(self.algorithm_set.keys())
        self.date_list = ["20200824", "20200825", "20200826", "20200827", "20200828",
                          "20200831", "20200901", "20200902", "20200903", "20200904",
                          "20200907"]
        self.date_list = ["20200911"]
        self.end_time_list = ['0910', '0915', '0920', '0930']
        self.volume_threshold_list = ['500k', '750k', '1M']

        self.invest_unit = 200000

        self.agent = Agent()

# endregion setting


# region DB Control

    def get_universe_list(self, date):
        logger.debug("get_universe_list")
        sql = "select code from " + date + "_setting_data"
        temp_list = self.engine_universe_new_rocket.execute(sql).fetchall()
        self.universe_list = [x[0] for x in temp_list]

    def get_one_code_data(self, date, code):
        sql = "select * from " + date + "_" + code
        data = self.engine_universe_new_rocket.execute(sql).fetchall()
        df_data = pd.DataFrame(data, columns=['index', 'time', 'code', 'price', 'volume',
                                               'hoga_sell_amount', 'hoga_buy_amount', 'open_price'])
        # print("!!!!!!!!!!!!!!!!!!!!!!!!! open_price 칼럼 순서 바꾸기 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        return df_data

    def get_one_code_data_to_csv(self, date, code):
        df_data = self.get_one_code_data(date, code)
        path = date + '_' + code + ".csv"
        print(df_data)
        df_data.to_csv(path_or_buf=path)

    def get_universe_list_tick_craw(self, date):
        logger.debug("get_universe_list")
        sql = "select code from " + date + "_setting_data where `check`=0"
        # sql = "select code from " + date + "_setting_data"
        temp_list = self.engine_tick_craw.execute(sql).fetchall()
        self.universe_list = [x[0] for x in temp_list]


    def result_summary_from_db_to_csv(self, table_name):
        sql = "select * from " + table_name
        data = simulator.engine_simulator_rocket.execute(sql).fetchall()
        df_data = pd.DataFrame(data, columns=['index'] + self.result_summary_column_list)
        path = table_name + ".csv"
        df_data.to_csv(path_or_buf=path)

# endregion DB Control

    def run_one_condition(self, consider_len, buy_discount_rate, sell_discount_rate, buy_power_threshold, sell_power_threshold, buy_accel_threshold, sell_accel_threshold, buy_power_ratio_threshold, over_open_price, date):
        # 시뮬레이션 조건별 이터레이션
        # 하나의 시뮬레이션 조건(파라미터 조합)에 대해 종목별 이터레이션 실시

        # 1일치의 종목별 이터레이션 결과 저장할 데이터프레임
        df_record = pd.DataFrame(columns=['trade_index', 'code', 'buy_time', 'sell_time', 'buy_price', 'sell_price',
                                          'amount', 'profit', 'earning_rate', 'geo_earning_rate', 'volume_first'])
        # 종목별 이터레이션
        trade_index = 0
        for code in self.universe_list:
            # state 생성
            state = State(code, code)
            possessed = False
            # universe_rocket db에서 데이터 가져옴
            data = self.get_one_code_data(date, code)
            # time step 이터레이션
            for i, row in data.iterrows():
                price = np.abs(row['price'])
                state.update_price(price)
                state.update_volume(row['volume'])
                state.update_open_price(np.abs(row['open_price']))

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
                        df_record.loc[trade_index, 'geo_earning_rate'] = sell_price * 0.9972 / buy_price

                        # 매도 했으면 trade_index +1
                        trade_index += 1

                # 보유하고 있지 않으면 매수 확인
                if not possessed:
                    if self.agent.check_buy_condition_simulation(state, consider_len, buy_discount_rate, buy_power_threshold, buy_power_ratio_threshold, buy_accel_threshold, over_open_price):
                        possessed = True
                        buy_num = int(np.round(self.invest_unit / state.price[-1]))
                        state.possessed_num = buy_num
                        # DB 처리, 계좌 처리
                        temp_dict = {'trade_index': trade_index,
                                     'code': code,
                                     'buy_time': row['time'],
                                     'buy_price': price,
                                     'amount': buy_num,
                                     'volume_first': state.volume[-consider_len]}
                        df_record = df_record.append(temp_dict, ignore_index=True)
            # 한 종목 이터레이션 끝났는데 매도 못 했으면 trade_index +1
            if possessed:
                trade_index += 1


        # 1일치 종목별 이터레이션 끝, record_summary에 저장할 정보 만듦
        df_record = df_record.fillna(0)
        df_record.drop(df_record[df_record['sell_price'] == 0].index, inplace=True)
        df_record.reset_index()
        return df_record

    def make_record_summary_to_db(self, df_record, param_list, param_value_tup, date):
        # record 요약 데이터 만들기

        # 필요한 column 생성
        # oscillation 개수, 비율 계산을 위한 timedelta
        df_record['timedelta'] = (df_record['sell_time'].apply(
            lambda x: datetime.strptime(str(x), '%Y%m%d%H%M%S')) - df_record[
                                   'buy_time'].apply(
            lambda x: datetime.strptime(str(x), '%Y%m%d%H%M%S'))).apply(
            lambda x: x.seconds)

        for vol_end_tup in itertools.product(self.volume_threshold_list, self.end_time_list):
            volume_threshold_str = vol_end_tup[0]
            if volume_threshold_str == self.volume_threshold_list[0]:
                volume_threshold = 500000
            elif volume_threshold_str == self.volume_threshold_list[1]:
                volume_threshold = 750000
            else:
                volume_threshold = 1000000
            end_time = vol_end_tup[1]

            # 정보 저장할 dictionary 생성
            result_dict = {}
            result_dict['end_time'] = [end_time]
            result_dict['volume_threshold'] = [volume_threshold_str]
            for param, value in zip(param_list, param_value_tup):
                result_dict[param] = [float(value)]

            # 특정 시간대까지의 기록만 남겨놓음
            end_time_detail = int(date + end_time + "00")
            temp_df_record = df_record[df_record['buy_time'].apply(lambda x: int(x)) <= end_time_detail]
            temp_df_record = temp_df_record[temp_df_record['volume_first'] >= volume_threshold]

            if len(temp_df_record) != 0:

                # 해당 시간대의 성과 지표 계산
                total_trade_count = len(temp_df_record)
                geo_profit = np.prod(temp_df_record['geo_earning_rate'])
                geo_mean_earning_rate = np.power(geo_profit, 1 / total_trade_count)
                mean_earning_rate = np.round(np.mean(temp_df_record['earning_rate']), 2)
                # oscillation_count = temp_df_record[(temp_df_record['timedelta'] <= 60) & (temp_df_record['earning_rate'] <= 0)].count()[0]
                # oscillation_ratio = np.round(oscillation_count / (total_trade_count + 0.00001), 2)
                # profit = np.round(mean_earning_rate * total_trade_count, 2)
                # 수익 개수, 수익률 평균, 손실 개수, 손실률 평균 계산
                # profit_trade_count = temp_df_record['earning_rate'][temp_df_record['earning_rate'] > 0].count()
                # profit_trade_mean_rate = np.round(temp_df_record['earning_rate'][temp_df_record['earning_rate'] > 0].mean(), 2)
                # loss_trade_count = temp_df_record['earning_rate'][temp_df_record['earning_rate'] <= 0].count()
                # loss_trade_mean_rate = np.round(temp_df_record['earning_rate'][temp_df_record['earning_rate'] <= 0].mean(), 2)
                # profit_loss_count_ratio = np.round(profit_trade_count / (loss_trade_count + 0.00001), 2)

                # 계산한 성능지표 result_dict에 저장
                result_dict['geo_profit'] = [geo_profit]
                result_dict['geo_mean_earning_rate'] = [geo_mean_earning_rate]
                result_dict['mean_earning_rate'] = [mean_earning_rate]
                result_dict['total_trade_count'] = [total_trade_count]
                # result_dict['oscillation_ratio'] = [oscillation_ratio]
                # result_dict['profit'] = [profit]
                # result_dict['profit_trade_count'] = [profit_trade_count]
                # result_dict['profit_trade_mean_rate'] = [profit_trade_mean_rate]
                # result_dict['loss_trade_count'] = [loss_trade_count]
                # result_dict['loss_trade_mean_rate'] = [loss_trade_mean_rate]
                # result_dict['profit_loss_count_ratio'] = [profit_loss_count_ratio]

                self.result_summary_column_list = list(result_dict.keys())

                df_result = pd.DataFrame(result_dict)
                check = len(df_result.dropna())
                result_summary_table_name = "result_summary_" + self.algorithm_set_name + "_" + date
                if check != 0:
                    df_result.to_sql(result_summary_table_name, self.engine_simulator_rocket, if_exists='append')

    def run(self):
        # 시간 체크
        temptime = time.time()
        # 날짜별로 시뮬레이션 실행
        for j, date in enumerate(self.date_list):
            # 해당 날짜의 종목 리스트 가져옴
            self.get_universe_list(date)
            # 해당 날짜에 시도하고자 하는 모든 파라미터의 조합으로 시뮬레이션 실행
            param_combination_list = list(itertools.product(*self.algorithm_set.values()))
            total_simulation_count = len(self.date_list) * len(param_combination_list)
            for i, tup in enumerate(param_combination_list):
                # 시뮬레이션 실행 및 기록 반환
                df_record = self.run_one_condition(*tup, date)
                # 시뮬레이션 성과지표 계산하여 DB에 저장
                if len(df_record) != 0:
                    self.make_record_summary_to_db(df_record, self.param_list, tup, date)

                print("시뮬레이션 진행률 : " + str(j*len(param_combination_list) + i + 1) + " / " + str(total_simulation_count) + ",  총 소요 시간 : " + str(np.round((time.time() - temptime) / 60, 2)) + " min")

            # 해당 날짜의 시뮬레이션 마쳤으면 summary 결과 csv 파일로 출력
            result_summary_table_name = "result_summary_" + self.algorithm_set_name + "_" + date
            self.result_summary_from_db_to_csv(result_summary_table_name)


if __name__ == "__main__":
    simulator = Simulator()
    simulator.run()

