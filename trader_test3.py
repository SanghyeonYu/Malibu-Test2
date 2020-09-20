# version 1.3.1
# -*- coding: utf-8 -*-
from library.open_api_test import *
from PyQt5.QtWidgets import *
import numpy as np

logger.debug("trader start !!!!!!")


class Trader(QMainWindow):
    def __init__(self):
        logger.debug("Trader __init__!!!")
        super().__init__()
        # 예제에 사용한 openapi는 사용하지 않습니다. library.open_api를 사용합니다.
        self.open_api = open_api()
        # 현재 시간을 저장
        self.current_time = QTime.currentTime()
        # 변수 설정 함수
        self.variable_setting()


    # 변수 설정 함수
    def variable_setting(self):
        self.open_api.py_gubun = "trader"
        self.condition_num = 0
        self.possessed_code_list = []
        self.invest_unit = 100000
        self.max_possess_num = 20
        ########## 매수 매도 알고리즘 번호 #############

        self.consider_len = 30
        self.algorithm_sell_num = 2
        self.algorithm_buy_num = 2

        ############################################

        ################ 장 시간 확인 ###################
        # # 장시작 시간 설정
        self.market_start_time = QTime(9, 0, 0)

        # 매수 중지 시간 설정
        self.trade_end_time = QTime(9, 10, 0)

        # 장마감 시간 설정
        self.market_end_time = QTime(15, 20, 0)

        # ############################################

        self.tick_1k = 5
        self.tick_5k = 10
        self.tick_10k = 50
        self.tick_50k = 100


    # 장시간 확인
    def market_time_check(self):
        logger.debug("market_time_check!!!")
        self.current_time = QTime.currentTime()
        if self.current_time > self.market_start_time and self.current_time < self.market_end_time:
            return True
        else:
            print("end!!!")
            return False


    def update_universe_list(self):
        # 조건 검색 수신, self.open_api.universe_list, self.open_api.universe 업데이트
        logger.debug("update_universe !!!! ")
        self.open_api.get_condition_load()
        self.open_api.send_condition("0150", self.open_api.condition_name_list[self.condition_num][1],
                                     self.open_api.condition_name_list[self.condition_num][0], 0)


    def update_universe(self):
        # 조건 검색 결과의 종목들에 대해 universe 정보 업데이트 진행
        logger.debug("update_universe!!!")
        # DB 업데이트를 위한 open_api.temp_data dictionary
        self.open_api.temp_data['time'] = [datetime.datetime.today().strftime("%Y%m%d%H%M%S")]
        code_list = self.open_api.universe_list
        code_list_reg = ';'.join(code_list)

        self.open_api.comm_kw_rq_data(code_list_reg, 0, int(len(code_list)), 0, "opt10001_req", "0101")
        time.sleep(0.21)
        self.open_api.comm_kw_rq_data(code_list_reg, 0, int(len(code_list)), 0, "opt10004_req", "0111")
        time.sleep(0.21)


    def auto_trade_sell(self, code_list):
        logger.debug("auto_trade_sell!!!!! 매도할 거 있나 체크!!!")
        for code in code_list:
            if self.open_api.agent.check_sell_condition_simulation(self.open_api.universe[code], consider_len=30, discount_rate=0.8, power_threshold=1, accel_threshold=0.7):
                # 매도!!

                logger.debug("send_order!!!!  code : " + str(code) + " number : " + str(self.open_api.universe[code].possessed_num))
                self.open_api.send_order("send_order_req", "0101", self.open_api.account_number, 2, code,
                                         self.open_api.universe[code].possessed_num, 0, "03", "")
                self.possessed_code_list.remove(code)
                self.open_api.universe[code].possessed_num = 0
                time.sleep(0.21)


    def sort_code_list_by_volume(self, code_list):
        temp_dict = dict()
        for code in code_list:
            # logger.debug(str(type(self.open_api.universe[code]['volume'][-1])) + str(self.open_api.universe[code]['volume'][-1]))
            if len(self.open_api.universe[code].volume) > 20:
                temp_dict[code] = self.open_api.universe[code].volume[-1]
        temp_list = sorted(temp_dict.items(), key=lambda x: x[1], reverse=True)
        temp_list2 = []
        for tup in temp_list:
            temp_list2.append(tup[0])
        return temp_list2

    def auto_trade_buy(self, code_list):
        for code in code_list:
            if len(self.possessed_code_list) == self.max_possess_num:
                break
            if code in self.possessed_code_list:
                continue
            if self.open_api.agent.check_buy_condition_simulation(self.open_api.universe[code], consider_len=30, discount_rate=0.5, power_threshold=10, power_ratio_threshold=20000, accel_threshold=0.33, over_open_price=True):
            # 매수 진행
                self.possessed_code_list.append(code)
                buy_num = int(np.round(self.invest_unit / self.open_api.universe[code].price[-1]))
                self.open_api.universe[code].possessed_num = buy_num
                self.open_api.universe[code].possessed_num = buy_num
                logger.debug("종목 매수 !!!!! 코드 : " + str(code) + "buy_num : " + str(buy_num))
                self.open_api.send_order("send_order_req", "0101", self.open_api.account_number, 1, code, buy_num, 0,
                                "03", "")
                time.sleep(0.21)


    def run(self):
        print("run함수에 들어왔습니다!")
        # 무한히 돌아라
        count = 0
        while 1:

            # 날짜 세팅
            self.open_api.date_setting()
            self.open_api.set_real_remove("ALL", "ALL")
            # 시간 체크
            if self.market_time_check():
                # 조건 검색 결과로 universe 목록, 정보 업데이트
                if count % 19 == 0:
                    self.update_universe_list()
                    time.sleep(0.21)

                self.update_universe()

                # logger.debug("time sleep 120~~")
                # time.sleep(120)


                # 업데이트된 정보를 바탕으로 매도 여부 판단 및 실행
                logger.debug("보유 종목!!!! : " + str(self.possessed_code_list))
                if len(self.possessed_code_list) != 0:
                    self.auto_trade_sell(self.possessed_code_list)

                # 업데이트된 정보를 바탕으로 매수 여부 판단 및 실행
                # universe에 종목이 하나라도 생기고, 매매 종료 기준 시간이 지나지 않은 경우 진행
                self.current_time = QTime.currentTime()
                if self.open_api.universe_list != ['0'] and self.current_time <= self.trade_end_time:
                    # 우선순위에 따라 종목 코드 리스트 정렬, 현재는 거래량
                    buy_check_list = self.sort_code_list_by_volume(self.open_api.universe_list)
                    logger.debug("universe_list!!!!" + str(self.open_api.universe_list))
                    self.auto_trade_buy(buy_check_list)

            # 5초를 판단 기준 단위로 삼음, 주문 및 조회 등 이벤트 여유 시간을 고려 4초 대기
            logger.debug("time sleep!! 4.5 seconds!!!    count : " + str(count) + "!!!")
            time.sleep(3.9)
            count += 1





if __name__ == "__main__":
    app = QApplication(sys.argv)
    trader = Trader()
    trader.run()

