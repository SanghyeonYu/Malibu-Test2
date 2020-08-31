from library.open_api_test import *
from PyQt5.QtWidgets import *
import numpy as np

logger.debug("api test !!!!!!")


class Trader(QMainWindow):
    def __init__(self):
        logger.debug("Trader __init__!!!")
        super().__init__()
        # 예제에 사용한 openapi는 사용하지 않습니다. library.open_api를 사용합니다.
        self.open_api = open_api()
        # 현재 시간을 저장
        self.current_time = QTime.currentTime()

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
        self.open_api.get_resistance("005930", "삼성전자")


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