from library.open_api_test import *
from PyQt5.QtWidgets import *
import numpy as np
import simulator_test2
import pandas as pd
import time
from datetime import datetime
from datetime import timedelta

logger.debug("api test !!!!!!")


class Trader(QMainWindow):
    def __init__(self):
        logger.debug("Trader __init__!!!")
        super().__init__()
        # 예제에 사용한 openapi는 사용하지 않습니다. library.open_api를 사용합니다.
        self.open_api = open_api()
        # 현재 시간을 저장
        self.current_time = QTime.currentTime()

        self.simulator = simulator_test2.Simulator()

        # self.date_list = ["20200824", "20200825", "20200826", "20200827", "20200828",
        #                   "20200831", "20200901", "20200902", "20200903", "20200904",
        #                   "20200907", "20200908", "20200909", "20200910", "20200911",
        #                   "20200914", "20200915"]
        # self.last_date_list = [                                                "20200821",
        #                        "20200824", "20200825", "20200826", "20200827", "20200828",
        #                        "20200831", "20200901", "20200902", "20200903", "20200904",
        #                        "20200907", "20200908", "20200909", "20200910", "20200911",
        #                        "20200914"]
        # self.date_list = ["20200907", "20200908", "20200909", "20200910", "20200911",
        #                   "20200914", "20200915"]
        # self.last_date_list = [                                                "20200904",
        #                        "20200907", "20200908", "20200909", "20200910", "20200911",
        #                        "20200914"]
        self.date_list = ["20200918"]
        self.last_date_list = ["20200917"]




        # rocket universe 데이터 csv 출력
        # code = "019170"
        # start_time = "20200824090000"
        # finish_time = "20200824094000"
        # sql = "select * from `" + code + "` where date >= " + start_time + " and date <= " + finish_time
        # data = self.open_api.engine_universe_rocket.execute(sql).fetchall()
        # df_data = pd.DataFrame(data, columns=['index', 'date', 'close', 'volume'])
        # print(df_data)
        # # path = code + ".csv"
        # # df_data.to_csv(path_or_buf=path)

        # region rocket start 조건 검색에 부합하는 종목 목록 universe_rocket db에 저장 (수정 : tick_craw)

        code_list = []
        candidates = {}
        for date in self.date_list:
            candidates[date] = {}
            candidates[date]['code'] = []
            candidates[date]['last_close'] = []
            sql = "select code, open from `" + date + "` where volume > " + "500000"
            temp_list = self.open_api.engine_daily_buy_list.execute(sql).fetchall()
            for tup in temp_list:
                # code_list.append(tup[0])
                candidates[date]['code'].append(tup[0])
                # candidates[date]['open'].append(tup[1])

        for last_date, date in zip(self.last_date_list, self.date_list):
            start_time = date + "0900"
            finish_time = date + "0930"
            for code in candidates[date]['code']:
                print(date, code)
                sql = "select close from `" + last_date + "` where code = " + code
                try:
                    yes_close = self.open_api.engine_daily_buy_list.execute(sql).fetchall()[0][0]
                    print(yes_close)
                except:
                    yes_close = 100000000
                    pass
                threshold = str(int(yes_close * 1.02))
                code_name = self.open_api.sf.get_name_by_code(code)
                if code_name == False:
                    continue
                sql = "select sum_volume from `" + code_name + "` where date >= " + start_time + " and date <= " + finish_time + " and sum_volume > " + "500000" + " and close >= " + threshold + " and close >= 1000" + " limit 1"
                temp = self.open_api.engine_craw.execute(sql).fetchall()
                if len(temp) != 0:
                    final_dict = {}
                    final_dict['date'] = [date]
                    final_dict['code'] = [code]
                    final_dict['code_name'] = [code_name]
                    final_dict['check'] = [0]
                    df_temp_data = pd.DataFrame(final_dict, columns=['date', 'code', 'code_name', 'check'])
                    df_temp_data.to_sql(date + "_setting_data", self.open_api.engine_tick_craw, if_exists='append')
                    df_temp_data.to_sql(date + "_setting_data", self.open_api.engine_universe_new_rocket, if_exists='append')
        # endregion

        #region 틱 데이터 크롤링
        code_list = []
        for date in self.date_list:
            self.simulator.get_universe_list_tick_craw(date)
            for code in self.simulator.universe_list:
                # # 테이블 존재하냐, 수정 필요
                # sql = "select 1 from information_schema.tables where table_schema ='tick_craw' and table_name = '{}'"
                # rows = self.open_api.engine_tick_craw.execute(sql.format(code)).fetchall()
                # if rows:
                #     logger.debug("이미 테이블 존재!!! code : " + str(code))
                # else:
                #     code_list.append(code)
                code_list.append(code)
        print(len(code_list))
        print(code_list)
        #
        # code_set = set(code_list)
        # # print(code_set)
        # print(len(code_set))
        #
        # sorted_code = list(pd.Series(list(code_set)).sort_values(ascending=True))
        # print(sorted_code)
        # print(len(sorted_code))
        # remain_code = sorted_code[:]
        # print(remain_code)
        # print(len(remain_code))
        # # remain_code = code_list

        for i, code in enumerate(code_list):
            self.open_api.get_total_data_tick(code, self.date_list[0])
            logger.debug(str(i+1) + "번째 완료!! code : " + str(code))
            if i % 25 == 24:
                time.sleep(90)
        #endregion 틱 데이터 크롤링

        # region 틱데이터 -> rocket universe 만들기
        for date in self.date_list:
            start_time_str = date + "090000"
            finish_time_str = date + "094000"

            self.simulator.get_universe_list(date)
            for code in self.simulator.universe_list:
                sql = "select * from `" + code + "` where date >= " + start_time_str + " and date <= " + finish_time_str
                data = self.open_api.engine_tick_craw.execute(sql).fetchall()
                df_data = pd.DataFrame(data, columns=['index', 'date', 'close', 'volume'])
                df_data.sort_values(by=['date'], inplace=True, ascending=True)
                df_data['date'] = df_data['date'].apply(lambda x: datetime.strptime(str(x), "%Y%m%d%H%M%S"))
                start_time = datetime.strptime(start_time_str, "%Y%m%d%H%M%S")
                finish_time = datetime.strptime(finish_time_str, "%Y%m%d%H%M%S")
                time_stamp_list = []
                for i in range(481):
                    time_stamp_list.append(start_time + timedelta(0, 5 * i))
                temp_df = pd.DataFrame(columns=['time', 'code', 'price', 'volume', 'hoga_sell_amount', 'hoga_buy_amount'])

                for stamp in time_stamp_list:
                    tempdict = {}
                    tempdict['time'] = datetime.strftime(stamp, "%Y%m%d%H%M%S")
                    tempdict['code'] = code
                    temp_list = list(df_data[df_data['date'] <= stamp]['close'])
                    if len(temp_list) != 0:
                        tempdict['price'] = temp_list[-1]
                    else:
                        continue
                    tempdict['volume'] = df_data[df_data['date'] <= stamp]['volume'].sum()
                    tempdict['hoga_sell_amount'] = 0
                    tempdict['hoga_buy_amount'] = 0
                    temp_df = temp_df.append(tempdict, ignore_index=True)
                temp_df.to_sql(date + "_" + code, self.open_api.engine_universe_new_rocket, if_exists='replace')
                logger.debug("create universe from tick data!!!! code : " + str(code))


        # endregion

        # region open_price 추가
        # for date in self.date_list:
        #     self.simulator.get_universe_list(date)
        #     for code in self.simulator.universe_list:
        #         sql = "select open from `" + date + "` where code = " + code
        #         open = self.open_api.engine_daily_buy_list.execute(sql).fetchall()[0][0]
        #
        #         sql = "alter table `" + '_'.join([date, code]) + "` add column open_price int"
        #         self.simulator.engine_universe_new_rocket.execute(sql)
        #
        #         sql = "update `" + '_'.join([date, code]) + "` set open_price = " + str(open) + " where code = " + code
        #         self.simulator.engine_universe_new_rocket.execute(sql)
        # endregion


        #region 조건 검색에서 검색 될 애들만 남김
        # for date in self.date_list:
        #     self.simulator.get_universe_list(date)
        #     for code in self.simulator.universe_list:
        #         table_name = '_'.join([date, code])
        #         sql = "select * from `" + table_name + "`"
        #         data = self.open_api.engine_universe_new_rocket.execute(sql).fetchall()
        #         df_data = pd.DataFrame(data, columns=['index', 'time', 'code', 'price', 'volume', 'hoga_sell_amount', 'hoga_buy_amount', 'open_price'])
        #         df_data.drop(['index'], axis=1, inplace=True)
        #         df_satisfied = df_data[(df_data['price'] > df_data['open_price'][0] * 1.02) & (df_data['volume'] >= 500000)]
        #         if len(df_satisfied) == 0:
        #             sql = "drop table " + table_name
        #             self.open_api.engine_universe_new_rocket.execute(sql)
        #             sql = "delete from `" + date + "_setting_data` where code = " + code
        #             self.open_api.engine_universe_new_rocket.execute(sql)
        #         # else:
        #             # start = df_satisfied.iloc[0]['time']
        #             # df_data = df_data[df_data['time'] >= start]
        #             # df_data.to_sql(table_name, self.open_api.engine_universe_new_rocket, if_exists='replace')

        #endregion










        # region 틱 데이터 날짜 순 정렬
        # code_list = []
        # for date in self.date_list:
        #     self.simulator.get_universe_list_tick_craw(date)
        #     for code in self.simulator.universe_list:
        #         code_list.append(code)
        #
        # code_set = set(code_list)
        # print(code_set)
        # print(len(code_set))
        # #
        # sorted_code = list(pd.Series(list(code_set)).sort_values(ascending=True))
        # print(sorted_code)
        # print(len(sorted_code))
        #
        # # sorted_code = ["005690"]
        # for i, code in enumerate(sorted_code):
        #     sql = "select * from `" + code + "` order by date asc"
        #     data = self.open_api.engine_tick_craw.execute(sql).fetchall()
        #     df_data = pd.DataFrame(data, columns=['index', 'date', 'close', 'volume'])
        #     df_data.drop(['index'], axis=1, inplace=True)
        #     df_data.to_sql(name=code, con=self.open_api.engine_tick_craw, if_exists='replace')
        #     logger.debug("update tick data by order!!!!  code : " + str(code) + "   " + str(i) + " / " + str(len(sorted_code)))


        # endregion





        ## 삼성 데이터 받아오기 테스트
        """
        self.open_api.py_gubun = "test"

        self.open_api.set_input_value("종목코드", "005930")
        self.open_api.set_input_value("기준일자", "20200826")
        self.open_api.set_input_value("수정주가구분", 1)

        # 아래에 이거 하나만 있고 while없애면 600일 한번만 가져오는거
        self.open_api.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

        print(self.open_api.ohlcv)
        """

        # DB 테스트
        # temp_list = ["005930", "112345"]
        # self.open_api.update_db_setting_data_universe_rocket(temp_list)
        # universe_list = self.open_api.get_universe_list(self.open_api.universe_list_table_name)
        # print(universe_list)
        # self.open_api.get_resistance("005930", "삼성전자")


        ## 실시간 검색 결과 받아오기 테스트
        # self.open_api.code_list = ["005930", "066570", "000270"]
        # self.open_api.code_list_reg = ';'.join(self.open_api.code_list)
        #
        # screen_no = "6001"
        #
        # # self.open_api.reg_callback("OnReceiveRealData", "", self.realtime_stream_callback)
        # logger.debug(str(self.open_api.fid_list_reg))
        # self.open_api.set_real_reg(screen_no, self.open_api.code_list_reg, self.open_api.fid_list_reg, 0)
        #
        # for i in range(10):
        #     logger.debug("iteration : " + str(i))
        #     self.open_api.make_event_loop()
        #
        #     logger.debug("time sleep!!" + str(QTime.currentTime()))
        #     time.sleep(1)
        #     logger.debug("time sleep!!" + str(QTime.currentTime()))

        ## 조건 검색 결과 받아오기 테스트
        # self.open_api.get_condition_load()
        # self.open_api.send_condition("0150", self.open_api.condition_name_list[1][1], self.open_api.condition_name_list[1][0], 0)
        # print(self.open_api.universe_list)
        #
        # resistance_list, last_price = self.get_resistance("032850")
        # print(resistance_list)
        # main_resistance = self.get_main_resistance(resistance_list, last_price)
        # print(main_resistance)



    tick_1 = 5
    tick_5 = 10
    tick_10 = 50
    tick_50 = 100














if __name__ == "__main__":
    app = QApplication(sys.argv)
    Trader()