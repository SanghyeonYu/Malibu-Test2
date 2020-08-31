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
        self.invest_unit = 200000
        ################ 모의, 실전 ####################
        # 장시작 시간 설정
        # self.market_start_time = QTime(9, 0, 0)
        # # 장마감 시간 설정
        # self.market_end_time = QTime(15, 30, 0)
        # # 매수를 몇 시 까지 할지 설정. (시, 분, 초)
        # self.buy_end_time = QTime(9, 6, 0)

        ############################################

        ################ 테스트용 ###################
        # # 장시작 시간 설정
        self.market_start_time = QTime(9, 0, 0)
        # 장마감 시간 설정
        self.market_end_time = QTime(15, 30, 0)

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

    def state_setting(self, code):
        new_state = defaultdict(deque)
        new_state['price'] = deque(['a' for _ in range(10)])
        new_state['price_velocity'] = deque(['a' for _ in range(10)])
        new_state['price_accel'] = deque(['a' for _ in range(10)])
        new_state['volume'] = deque(['a' for _ in range(10)])
        new_state['volume_velocity'] = deque(['a' for _ in range(10)])
        new_state['volume_var'] = deque(['a' for _ in range(10)])
        new_state['hoga_sell_ratio'] = deque(['a' for _ in range(10)])
        new_state['possessed_num'] = 0
        return new_state

    def update_universe_list(self):
        # 조건 검색 수신
        logger.debug("update_universe !!!! ")
        self.open_api.get_condition_load()
        self.open_api.send_condition("0150", self.open_api.condition_name_list[self.condition_num][1],
                                     self.open_api.condition_name_list[self.condition_num][0], 0)
        self.open_api.universe_list = self.open_api.universe_list[:100] if len(
            self.open_api.universe_list) > 100 else self.open_api.universe_list

        self.open_api.universe = dict()

        for code in self.open_api.universe_list:
            if code not in self.open_api.universe:
                self.open_api.universe[code] = self.state_setting(code)



    def update_universe(self):
        # 조건 검색 결과의 종목들에 대해 universe 정보 업데이트 진행
        logger.debug("update_universe!!!")
        code_list = self.open_api.universe_list
        code_list_reg = ';'.join(code_list)

        self.open_api.comm_kw_rq_data(code_list_reg, 0, int(len(code_list)), 0, "opt10001_req", "0101")
        time.sleep(0.21)
        self.open_api.comm_kw_rq_data(code_list_reg, 0, int(len(code_list)), 0, "opt10004_req", "0101")
        time.sleep(0.21)

        #저항구간
        for code in self.open_api.universe_list:
            if 'resistance_list' not in self.open_api.universe[code]:
                if self.get_resistance(code) != False and self.open_api.universe[code]['price'][-1] != 'a':
                    resistance_list, last = self.get_resistance(code)
                    main_resistance = self.get_main_resistance(resistance_list, self.open_api.universe[code]['price'][-1])
                    self.open_api.universe[code]['resistance_list'] = deque(resistance_list)
                    self.open_api.universe[code]['main_resistance'] = main_resistance
                    logger.debug("현재가 : " + str(self.open_api.universe[code]['price'][-1]) + "    저항선 : " + str(main_resistance))
                    self.open_api.universe[code]['threshold'] = self.get_threshold(main_resistance)
                    # logger.debug("get_resistance!! : " + str(self.open_api.universe[code]['main_resistance']))

        # 실시간 일단 버리자
        # # set_real_reg 안에서 조회한 정보로 universe 정보 업데이트 실행
        # self.open_api.set_real_reg("6001", code_list_reg, self.open_api.fid_list_reg, 0)
        # # 연결 해제
        # self.open_api.set_real_remove("ALL", "ALL")





    # 1년치 일봉데이터로 기준선 만들기
    def get_resistance(self, code):
        code_name = self.open_api.sf.get_name_by_code(code)
        if code_name == False:
            self.open_api.universe_list.remove(code)
            logger.debug("!!! 목록에 없는 종목인데 ???? !!!!  : " + str(code))
            return False
        sql = "select open, high, low, close from `" + code_name + "` where date >= 20190828"
        temp_list = self.open_api.engine_daily_craw.execute(sql).fetchall()
        ohlc_list = []
        for tup in temp_list:
            ohlc_list += list(tup)
        ohlc_np = np.array(ohlc_list)

        last = ohlc_np[-1]
        min = np.min(ohlc_np)
        max = np.max(ohlc_np)

        if last < 3000:
            delta = 250
            if max >= 5000:
                delta = 500
        elif last >= 3000 and last < 20000:
            delta = 500
        else:
            delta = 1000

        resistance_min = np.floor(min / delta) * delta
        resistance_max = np.ceil(max / delta) * delta
        resistance_num = (resistance_max - resistance_min) / delta + 1
        resistance_list = [x * delta + resistance_min for x in range(int(resistance_num))]
        # resistance_list.append(max)

        # res_count_list = []
        # for res in resistance_list:
        #     lower_bound = res - delta * 0.3
        #     upper_bound = res + delta * 0.3
        #     count = ((lower_bound <= ohlc_np) & (ohlc_np <= upper_bound)).sum()
        #     res_count_list.append(count)
        # print(resistance_list)
        # print(res_count_list)

        return resistance_list, last

    def get_main_resistance(self, resistance_list, price):
        temp_np = np.array([x - price for x in resistance_list])
        main_resistance = resistance_list[np.where(temp_np > 0, temp_np, np.inf).argmin()]
        return main_resistance

    def get_threshold(self, main_resistance):
        if main_resistance <= 5000:
            threshold = main_resistance + self.tick_1k * 3
        elif main_resistance <=10000:
            threshold = main_resistance + self.tick_5k * 3
        elif main_resistance <=50000:
            threshold = main_resistance + self.tick_10k * 3
        else:
            threshold = main_resistance + self.tick_5k * 3
        return threshold

    def check_sell_condition(self, state):
        points = 0
        weight = 0

        if state['price'][-3] == 'a':
            return False

        if state['volume_var'][-1] >= 1.2:
            weight = 3
        elif state['volume_var'][-1] < 1.2 and state['volume_var'][-1] >= 0.84:
            weight = 1
        elif state['volume_var'][-1] < 0.84:
            weight = 2

        if state['price'][-1] <= state['main_resistance']:
            return True

        if state['price_velocity'][-1] >= 0:
            if state['price_velocity'][-1] * 3 + state['price_accel'][-1] < 0 and state['volume_var'][-1] < 0.5 and state['hoga_sell_ratio'][-1] <= 0.55:
                return True
            return False
        else:
            if state['price_velocity'][-2] < 0 and weight == 2:
                return True
            points += weight

        if state['hoga_sell_ratio'][-1] <= 0.55:
            points += 2
        elif state['hoga_sell_ratio'][-1] <= 0.7:
            points += 1

        if points >= 3:
            return True

        return False

    def auto_trade_sell(self, code_list):
        logger.debug("auto_trade_sell!!!!! 매도할 거 있나 체크!!!")
        temp_list = []
        temp_list += code_list
        for code in temp_list:
            if self.check_sell_condition(self.open_api.universe[code]):
                # 매도!!
                self.possessed_code_list.remove(code)
                logger.debug("send_order!!!!  code : " + str(code) + " number : " + str(self.open_api.universe[code]['possessed_num']))
                self.open_api.send_order("send_order_req", "0101", self.open_api.account_number, 2, code,
                                         self.open_api.universe[code]['possessed_num'], 0, "03", "")
                time.sleep(0.21)



    def sort_code_list_by_volume(self, code_list):
        temp_dict = dict()
        for code in code_list:
            # logger.debug(str(type(self.open_api.universe[code]['volume'][-1])) + str(self.open_api.universe[code]['volume'][-1]))
            if self.open_api.universe[code]['volume'][-1] != 'a':
                temp_dict[code] = self.open_api.universe[code]['volume'][-1]
        temp_list = sorted(temp_dict.items(), key=lambda x: x[1], reverse=True)
        temp_list2 = []
        for tup in temp_list:
            temp_list2.append(tup[0])
        return temp_list2

    def auto_trade_buy(self, code_list):
        # buy_lock = False

        for code in code_list:
            state = self.open_api.universe[code]
            if len(self.possessed_code_list) == 5:
                break
            if code in self.possessed_code_list:
                continue
            if state['price'][-3] == 'a':
                continue
            if state['price'][-3] != 'a' and state['price'][-3] >= state['main_resistance']:
                continue
                # if state['price_velocity'][-1] * 4 + state['price_accel'][-1] >= 0 and state['volume_var'][-1] >= 1.2:
                #     pass
                # else:
                #     continue

            if state['price_velocity'][-1] * 3 + state['price_accel'][-1] < 0 and state['volume_var'][-1] < 0.5 and state[
                'hoga_sell_ratio'][-1] <= 0.55:
                continue

            if state['price'][-1] >= state['threshold']:
                pass
            else:
                continue
            if state['price_velocity'][-1] > 0:
                pass
            else:
                continue

            # 매수 진행
            logger.debug("현재 state 조회!!!! price : " + str(state['price']) + "velocity : " + str(state['price_velocity']) + "accel : " + str(state['price_accel']))
            self.possessed_code_list.append(code)
            buy_num = int(np.round(self.invest_unit / state['price'][-1]))
            self.open_api.universe[code]['possessed_num'] = buy_num
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
            # self.open_api.set_real_remove("ALL", "ALL")
            # 시간 체크
            if self.market_time_check():
                # universe 목록, 정보 업데이트
                if count % 20 == 0:
                    self.update_universe_list()
                    if '' in self.open_api.universe_list:
                        self.open_api.universe_list.remove('')
                    time.sleep(0.21)

                self.update_universe()
                self.open_api.universe_list = self.sort_code_list_by_volume(self.open_api.universe_list)

                # logger.debug("time sleep 120~~")
                # time.sleep(120)

                for code in self.open_api.universe_list:
                    state = self.open_api.universe[code]
                    logger.debug("!!!!!!!! 정보확인 !!!!!!    종목코드 : " + str(code))
                    logger.debug("!!!!!!!! 정보확인 !!!!!!    현재가 : " + str(state['price'][-1]))
                    logger.debug("!!!!!!!! 정보확인 !!!!!!    저항선 : " + str(state['main_resistance']))
                    logger.debug("!!!!!!!! 정보확인 !!!!!!    매도비율 : " + str(state['hoga_sell_ratio'][-1]))

                # 업데이트된 정보를 바탕으로 매도 여부 판단 및 실행
                logger.debug("보유 종목!!!! : " + str(self.possessed_code_list))
                if len(self.possessed_code_list) != 0:
                    self.auto_trade_sell(self.possessed_code_list)

                # 업데이트된 정보를 바탕으로 매수 여부 판단 및 실행
                # 우선순위에 따라 종목 코드 리스트 정렬
                logger.debug("universe_list!!!!" + str(self.open_api.universe_list))
                self.auto_trade_buy(self.open_api.universe_list)

            # 10초를 판단 기준 단위로 삼음, 주문 및 조회 등 이벤트 여유 시간을 고려 9초 대기
            logger.debug("time sleep!! 9 seconds!!")
            time.sleep(9)
            count += 1





if __name__ == "__main__":
    app = QApplication(sys.argv)
    trader = Trader()
    trader.run()

