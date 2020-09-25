import os
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from tensorflow.keras import Sequential
from tensorflow.keras.layers import LSTM, Dense, TimeDistributed
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import ModelCheckpoint, TensorBoard

df = pd.read_csv("./data./sub_labeled.csv")
data = df.loc[:, ["labor_rate_{0}".format(i) for i in range(10)]].to_numpy()[:, :, np.newaxis]
X, y = data[:, :-1], data[:, 1:]
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

model = Sequential([
    LSTM(100, return_sequences=True, input_shape=[None, 1]),
    LSTM(100, return_sequences=True),
    LSTM(100, return_sequences=True),
    TimeDistributed(Dense(1))
])

optimizer = Adam(lr=0.001)
model.compile(loss='mse', optimizer=optimizer)

model_path = "./model"
summary_path = "./summary"

if not os.path.exists(model_path):
    os.makedirs(model_path)

if not os.path.exists(summary_path):
    os.makedirs(summary_path)

checkpoint_cb = ModelCheckpoint(model_path + "/test.h5", save_best_only=True)
tensorboard_cb = TensorBoard(summary_path + "/test.h5")

history = model.fit(X_train, y_train, validation_split=0.2, epochs=1000, callbacks=[checkpoint_cb, tensorboard_cb])

mse = model.evaluate(X_test, y_test)
print(mse)