from tensorflow import keras
from tensorflow.keras.layers import LSTM, Dense, TimeDistributed


class RNN_Model(keras.Model):
    def __init__(self, n_units1, n_units2, n_units3, n_units4, layer_num, **kwargs):
        super().__init__(**kwargs)
        self.hidden1 = LSTM(n_units1, return_sequences=True)
        self.hidden2 = LSTM(n_units2, return_sequences=True)
        self.hidden3 = LSTM(n_units3, return_sequences=True)
        self.hidden4 = LSTM(n_units4, return_sequences=True)
        self.out = TimeDistributed(Dense(1))

        self.layer_num = layer_num

    def call(self, inputs):
        hidden1 = self.hidden1(inputs)
        if self.layer_num == 2:
            return self.out(hidden1)
        hidden2 = self.hidden2(hidden1)
        if self.layer_num == 3:
            return self.out(hidden2)
        hidden3 = self.hidden3(hidden2)
        if self.layer_num == 4:
            return self.out(hidden3)
        hidden4 = self.hidden4(hidden3)
        if self.layer_num == 5:
            return self.out(hidden4)