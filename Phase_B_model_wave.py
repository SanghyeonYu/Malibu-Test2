from tensorflow import keras
from tensorflow.keras.layers import LSTM, Dense, TimeDistributed
import numpy as np
import tensorflow as tf

class GatedActivationUnit(keras.layers.Layer):
    def __init__(self, activation="tanh", **kwargs):
        super().__init__(**kwargs)
        self.activation = keras.activations.get(activation)
    def call(self, inputs):
        n_filters = inputs.shape[-1] // 2
        linear_output = self.activation(inputs[..., :n_filters])
        gate = keras.activations.sigmoid(inputs[..., n_filters:])
        return self.activation(linear_output) * gate

def wavenet_residual_block(inputs, n_filters, dilation_rate):
    z = keras.layers.Conv1D(2 * n_filters, kernel_size=2, padding="causal",
                            dilation_rate=dilation_rate)(inputs)
    z = GatedActivationUnit()(z)
    z = keras.layers.Conv1D(n_filters, kernel_size=1)(z)
    return keras.layers.Add()([z, inputs]), z

keras.backend.clear_session()
np.random.seed(42)
tf.random.set_seed(42)

n_layers_per_block = 9 # 10 in the paper
n_blocks = 3 # 3 in the paper
n_filters = 64 # 128 in the paper
n_outputs = 3 # 256 in the paper


input_sec = keras.layers.Input(shape=(420, 2))
# print(inputs)
z = keras.layers.Conv1D(n_filters * 2, kernel_size=2, padding="causal")(input_sec)
# print(z)
z = keras.layers.Conv1D(n_filters, kernel_size=2, padding="causal")(z)
skip_to_last = []
for dilation_rate in [2**i for i in range(n_layers_per_block)] * n_blocks:
    z, skip = wavenet_residual_block(z, n_filters, dilation_rate)
    skip_to_last.append(skip)
z = keras.activations.relu(keras.layers.Add()(skip_to_last))
z = keras.layers.Conv1D(n_filters, kernel_size=1, activation="relu")(z)
print(z)
input_vol = keras.layers.Input(shape=(40, 2))


# print(z)
Y_proba = keras.layers.Conv1D(n_outputs, kernel_size=1, activation="sigmoid")(z)
# print(Y)

model = keras.models.Model(inputs=[input_sec], outputs=[Y_proba])


class WAVE_Net(keras.Model):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.wave_net = model

    def call(self, inputs):
        return self.wave_net(inputs)




#
# class WAVE_Net(keras.Model):
#     def __init__(self, n_units1, n_units2, n_units3, n_units4, layer_num, **kwargs):
#         super().__init__(**kwargs)
#         self.hidden1 = LSTM(n_units1, return_sequences=True)
#         self.hidden2 = LSTM(n_units2, return_sequences=True)
#         self.hidden3 = LSTM(n_units3, return_sequences=True)
#         self.hidden4 = LSTM(n_units4, return_sequences=True)
#         self.out = TimeDistributed(Dense(1))
#
#         self.layer_num = layer_num
#
#     def call(self, inputs):
#         hidden1 = self.hidden1(inputs)
#         if self.layer_num == 2:
#             return self.out(hidden1)
#         hidden2 = self.hidden2(hidden1)
#         if self.layer_num == 3:
#             return self.out(hidden2)
#         hidden3 = self.hidden3(hidden2)
#         if self.layer_num == 4:
#             return self.out(hidden3)
#         hidden4 = self.hidden4(hidden3)
#         if self.layer_num == 5:
#             return self.out(hidden4)