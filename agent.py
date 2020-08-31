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
        self.price.append(data)
        if len(self.price) > 60:
            self.price.popleft()
        # price_velocity, price_accel 업데이트
        if len(self.price) >= 2:
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

    def update_hoga_amount(self, hoga_sell_amount, hoga_buy_amount):
        self.hoga_sell_amount.append(hoga_sell_amount)
        self.hoga_buy_amount.append(hoga_buy_amount)
        if hoga_sell_amount !=0 and hoga_buy_amount !=0:
            self.hoga_sell_ratio.append(hoga_sell_amount / hoga_buy_amount)
            self.hoga_buy_ratio.append(hoga_buy_amount / hoga_sell_amount)
        if len(self.hoga_sell_amount) > 60:
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

    def check_sell_condition(self, state):
        # 상승하는 힘 < 하락하는 힘이면 팔 것
        np_pv = np.array(state.price_velocity)
        np_vv = np.array(state.volume_velocity)
        np_pv = np_pv[-19:]
        np_vv = np_vv[-19:]
        power = np.dot(np_pv, np_vv)
        if power > 0:
            # 가속도가
            np_pa = np.array(state.price_accel)
            np_pa = np_pa[-19:]
            if (np_pa < 0).sum() >= 12:
                return True
            return False
        else:
            return True

    def check_buy_condition(self, state):
        # 100초는 관찰한 후에 살 것
        if len(state.price) < 20:
            return False

        # 저항선 돌파 이후에 살 것
        if np.mean([state.price[-20], state.price[-1]]) < state.main_resistance:
            return False

        # 상승하는 힘 > 하락하는 힘일 때 살 것
        np_pv = np.array(state.price_velocity)
        np_vv = np.array(state.volume_velocity)
        np_pv = np_pv[-19:]
        np_vv = np_vv[-19:]
        power = np.dot(np_pv, np_vv)
        if power <= 0:
            return False

        # 가속도가 붙어 있을 때 살 것
        np_pa = np.array(state.price_accel)
        np_pa = np_pa[-19:]
        if (np_pa >= 0).sum() < 8:
            return False

        return True


if __name__ == "__main__":
    print()
