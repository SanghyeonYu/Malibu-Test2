
print("collector 프로그램이 시작 되었습니다!")

from library.collector_api_test import *
import pymysql
pymysql.install_as_MySQLdb()

class Collector:
    print("collector 클래스에 들어왔습니다.")

    def __init__(self):
        print("__init__ 함수에 들어왔습니다.")

        self.collector_api = collector_api()
        #코스피, 코스닥 종목 출력 테스트

    def collecting(self):
        self.collector_api.code_update_check()

    def tick_collecting(self):
        self.collector_api.db_to_tick_craw



print("collector.py 의 __name__ 은?: ", __name__)
if __name__ == "__main__":
    print("__main__에 들어왔습니다.")
    app = QApplication(sys.argv)
    # c = Collector()

    # c.collecting()
