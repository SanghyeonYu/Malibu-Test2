import pandas as pd
import numpy as np
from collections import deque

from library import cf
from sqlalchemy import create_engine, event

class State():
    def __init__(self, code, code_name):
        self.code = code
        self.code_name = code_name
        self.yes_close = 0
        self.open_price = 0

        self.price = deque()
        self.price_velocity = deque()
        self.price_accel = deque()

        self.volume = deque()
        self.volume_velocity = deque()
        self.volume_var = deque()

        self.hoga_sell_amount = deque()
        self.hoga_buy_amount = deque()
        self.hoga_sell_ratio = deque()
        self.hoga_buy_ratio = deque()

        self.resistance_list = []
        self.main_resistance = np.inf

        self.possessed_num = 0

    def update_price(self, data):
        # print(self.price)
        self.price.append(data)
        # print(self.price)
        if len(self.price) > 60:
            self.price.popleft()
        # price_velocity, price_accel 업데이트
        if len(self.price) >= 2:
            # print(self.price)
            self.price_velocity.append(self.price[-1] - self.price[-2])
            if len(self.price_velocity) > 60:
                self.price_velocity.popleft()
        if len(self.price_velocity) >= 2:
            self.price_accel.append(self.price_velocity[-1] - self.price_velocity[-2])
            if len(self.price_accel) > 60:
                self.price_accel.popleft()

    def update_volume(self, data):
        self.volume.append(data)
        if len(self.volume) > 60:
            self.volume.popleft()
        # volume_velocity, volume_accel 업데이트
        if len(self.volume) >= 2:
            self.volume_velocity.append(self.volume[-1] - self.volume[-2])
            if len(self.volume_velocity) > 60:
                self.volume_velocity.popleft()
        if len(self.volume_velocity) >= 2:
            if self.volume_velocity[-2] != 0:
                self.volume_var.append(self.volume_velocity[-1] / self.volume_velocity[-2])
            else:
                self.volume_var.append(0)
            if len(self.volume_var) > 60:
                self.volume_var.popleft()

    def update_open_price(self, data):
        self.open_price = data

    def update_hoga_amount(self, hoga_sell_amount, hoga_buy_amount):
        self.hoga_sell_amount.append(hoga_sell_amount)
        self.hoga_buy_amount.append(hoga_buy_amount)
        if hoga_sell_amount !=0 and hoga_buy_amount !=0:
            self.hoga_sell_ratio.append(hoga_sell_amount / hoga_buy_amount)
            self.hoga_buy_ratio.append(hoga_buy_amount / hoga_sell_amount)
        if len(self.hoga_sell_amount) > 60 and len(self.hoga_buy_amount) > 60:
            self.hoga_sell_amount.popleft()
            self.hoga_buy_amount.popleft()
            self.hoga_sell_ratio.popleft()
            self.hoga_buy_ratio.popleft()

    def update_main_resistance(self):
        if len(self.price) > 0:
            price = self.price[-1]
            if price > self.main_resistance:
                temp_np = np.array([x - price for x in self.resistance_list])
                next_resistance = self.resistance_list[np.where(temp_np > 0, temp_np, np.inf).argmin()]
                if (next_resistance - price) < (price - self.main_resistance):
                    self.main_resistance = next_resistance

class Agent():
    def __init__(self):
        pass

    def check_sell_condition(self, state, consider_len, algorithm_num):
        # 매수 / 매도 결정에 고려할 time step 개수 : consider_len
        # velocity 개수 : n
        n = consider_len - 1

        # 매수 / 매도 결정에 고려할 price, volume velocity ndarray로 저장
        np_pv = np.array(state.price_velocity)
        np_vv = np.array(state.volume_velocity)
        np_pa = np.array(state.price_accel)
        np_pv = np_pv[-n:]
        np_vv = np_vv[-n:]
        np_pa = np_pa[-(n-1):]

        if algorithm_num == 1:
            # 상승하는 힘 < 하락하는 힘이면 팔 것
            power = np.dot(np_pv, np_vv)
            if power > 0:
                # 가속도가
                if (np_pa < 0).sum() >= 12:
                    return True
                return False
            else:
                return True

        elif algorithm_num == 2:
            # 할인율 적용
            discount_rate = 0.9
            discount_factor = np.power([discount_rate for _ in range(n)], [n - 1 - i for i in range(n)])
            # 상승, 하락 힘 계산
            np_power = np_pv * np_vv * discount_factor
            power_rise = np_power[(np_power >= 0)].sum()
            power_fall = np.abs(np_power[(np_power < 0)].sum())
            # 매도 조건은 유사시에 금방 팔 수 있게 threshold 낮춰줌
            if power_rise / (power_fall + 0.00001) <= 1.0:
                power_check = True
            else:
                power_check = False
            # 하방 가속도가 붙은 경우 팔 것
            if (np_pa < 0).sum() / len(np_pa) >= 0.75:
                accel_check = True
            else:
                accel_check = False
            temp_pa = np_pa[-5:]
            if (temp_pa < 0).sum() / len(temp_pa) >= 0.8:
                accel_check_2 = True
            else:
                accel_check_2 = False

            # 유사시에는 빠른 매도 필요
            if power_check or accel_check or accel_check_2:
                return True
            else:
                return False

        else:
            print("올바른 매도 알고리즘 번호 지정 필요!!!!!!!!!")

    def check_buy_condition(self, state, consider_len, algorithm_num):
        # 매수 / 매도 결정에 고려할 time step 개수 : consider_len
        # velocity 개수 : n
        n = consider_len - 1
        # 최소 time step만큼 관찰한 후에 살 것
        if len(state.price) < consider_len:
            return False

        # 매수 / 매도 결정에 고려할 price, volume velocity ndarray로 저장
        np_pv = np.array(state.price_velocity)
        np_vv = np.array(state.volume_velocity)
        np_pa = np.array(state.price_accel)
        np_pv = np_pv[-n:]
        np_vv = np_vv[-n:]
        np_pa = np_pa[-(n-1):]

        if algorithm_num == 1:
            # 저항선 돌파 이후에 살 것
            if np.mean([state.price[-n], state.price[-1]]) < state.main_resistance:
                return False
            # 상승하는 힘 > 하락하는 힘일 때 살 것
            power = np.dot(np_pv, np_vv)
            if power <= 0:
                return False
            # 가속도가 붙어 있을 때 살 것
            if (np_pa >= 0).sum() < 8:
                return False
            return True

        elif algorithm_num == 2:
            # 할인율 적용
            discount_rate = 0.95
            discount_factor = np.power([discount_rate for _ in range(n)], [n - 1 - i for i in range(n)])
            # 상승, 하락 힘 계산
            np_power = np_pv * np_vv * discount_factor
            power_rise = np_power[(np_power >= 0)].sum()
            power_fall = np.abs(np_power[(np_power < 0)].sum())
            # 강한 상승이 있을 땐 필히 거래량을 동반해야 하므로, 진동 방지를 위해 threshold가 좀 높아도 괜찮다.
            if power_rise / (power_fall + 0.00001) > 2:
                power_check = True
            else:
                power_check = False
            # 가속도가 붙어 있을 때 살 것
            if (np_pa > 0).sum() / len(np_pa) > 0.33:
                accel_check = True
            else:
                accel_check = False

            # 일단 매매하는 순간 수수료 손실이 생기므로 매수는 신중하게
            if power_check and accel_check:
                return True
            else:
                return False

        else:
            print("올바른 매수 알고리즘 번호 지정 필요!!!!!!!!!")

    def check_sell_condition_simulation(self, state, consider_len, discount_rate, power_threshold, accel_threshold):
        # 매수 / 매도 결정에 고려할 time step 개수 : consider_len
        # velocity 개수 : n
        n = consider_len - 1

        # 매수 / 매도 결정에 고려할 price, volume velocity ndarray로 저장
        np_pv = np.array(state.price_velocity)
        np_vv = np.array(state.volume_velocity)
        np_pa = np.array(state.price_accel)
        np_pv = np_pv[-n:]
        np_vv = np_vv[-n:]
        np_pa = np_pa[-(n-1):]
        # 할인율 적용
        discount_rate = discount_rate
        discount_factor = np.power([discount_rate for _ in range(n)], [n - 1 - i for i in range(n)])
        # 상승, 하락 힘 계산
        np_power = np_pv * np_vv * discount_factor
        power_rise = np_power[(np_power >= 0)].sum()
        power_fall = np.abs(np_power[(np_power < 0)].sum())
        # 매도 조건은 유사시에 금방 팔 수 있게 threshold 낮춰줌
        if power_rise / (power_fall + 0.00001) <= power_threshold:
            power_check = True
        else:
            power_check = False
        # 하방 가속도가 붙은 경우 팔 것
        if (np_pa < 0).sum() / len(np_pa) >= accel_threshold:
            accel_check = True
        else:
            accel_check = False
        temp_pa = np_pa[-5:]
        if (temp_pa < 0).sum() / len(temp_pa) >= 0.8:
            accel_check_2 = True
        else:
            accel_check_2 = False

        # 유사시에는 빠른 매도 필요
        if power_check or accel_check or accel_check_2:
            return True
        else:
            return False


    def check_buy_condition_simulation(self, state, consider_len, discount_rate, power_threshold, power_ratio_threshold, accel_threshold, over_open_price):
        # 매수 / 매도 결정에 고려할 time step 개수 : consider_len
        # velocity 개수 : n
        n = consider_len - 1
        # 최소 time step만큼 관찰한 후에 살 것
        if len(state.price) < consider_len:
            return False
        # open_price = True이면, 현재가가 시가보다 낮으면 사지 말 것
        if over_open_price == True and np.abs(state.open_price) > state.price[-1]:
            return False

        # 매수 / 매도 결정에 고려할 price, volume velocity ndarray로 저장
        np_pv = np.array(state.price_velocity)
        np_vv = np.array(state.volume_velocity)
        np_pa = np.array(state.price_accel)
        np_pv = np_pv[-n:]
        np_vv = np_vv[-n:]
        np_pa = np_pa[-(n-1):]

        # 할인율 적용
        discount_rate = discount_rate
        discount_factor = np.power([discount_rate for _ in range(n)], [n - 1 - i for i in range(n)])
        # 상승, 하락 힘 계산
        np_power = np_pv * np_vv * discount_factor
        power_rise = np_power[(np_power >= 0)].sum()
        power_fall = np.abs(np_power[(np_power < 0)].sum())
        # 매수 조건
        if power_rise / (power_fall + 0.00001) > power_threshold:
            power_check = True
        else:
            power_check = False
        # 가속도가 붙어 있을 때 살 것
        if (np_pa > 0).sum() / len(np_pa) >= accel_threshold:
            accel_check = True
        else:
            accel_check = False
        # 최근 상승힘의 크기가 과거 상승힘의 크기보다 클 때 살 것
        half = int(np.ceil(n/2))
        power_old = np_power[:half]
        power_old = power_old[(power_old >= 0)].sum()
        power_recent = np_power[half:]
        power_recent = power_recent[(power_recent >= 0)].sum()
        if power_recent / (power_old + 0.00001) > power_ratio_threshold:
            power_ratio_check = True
        else:
            power_ratio_check = False

        # 일단 매매하는 순간 수수료 손실이 생기므로 매수는 신중하게
        if power_check and accel_check and power_ratio_check:
            return True
        else:
            return False


if __name__ == "__main__":
    print()
