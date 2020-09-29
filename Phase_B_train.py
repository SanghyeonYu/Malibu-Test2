import os
import numpy as np
import pandas as pd
import time

import tensorflow as tf
# GPU 메모리 증가 허용
physical_devices = tf.config.list_physical_devices('GPU')
try:
    print("memory_growth!!")
    tf.config.experimental.set_memory_growth(physical_devices[0], True)
except:
    print("!!!!!!!!!")
  # Invalid device or cannot modify virtual devices once initialized.
    pass

from tensorflow import keras
from Phase_B_Data_Loader import *
from sklearn.model_selection import train_test_split
from tensorflow.keras.optimizers import Adam, Adadelta, RMSprop
from tensorflow.keras.models import load_model
from tensorflow.keras.callbacks import ModelCheckpoint, TensorBoard, EarlyStopping

import Phase_B_model_wave as wave_net



if __name__ == "__main__":
    # 데이터 로드
    data_loader = Data_Loader()
    data_volume_profile, data_sec_data, data_label = data_loader.get_stacked_dataset()
    # print(data_volume_profile.shape)
    # print(data_volume_profile[0])
    # print(data_sec_data.shape)
    # print(data_sec_data[0])
    # print(data_label.shape)
    # print(data_label[0][:50])

    tf.random.set_seed(42)
    data_volume_profile = tf.random.shuffle(data_volume_profile)
    tf.random.set_seed(42)
    data_sec_data = data_sec_data[:, :420, :]
    data_sec_data = tf.random.shuffle(data_sec_data)
    tf.random.set_seed(42)
    data_label = data_label[:, :, :2]
    data_label = tf.random.shuffle(data_label)

    sample_num = len(data_label)
    test_size = 0.1
    train_num = int((1 - test_size) * sample_num)

    X_train_vol, X_train_sec, y_train = data_volume_profile[:train_num], data_sec_data[:train_num], data_label[:train_num]
    X_test_vol, X_test_sec, y_test = data_volume_profile[train_num:], data_sec_data[train_num:], data_label[train_num:]

    # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1)

    load = False
    model_path = "./model_B"
    summary_path = "./summary_B"

    if not os.path.exists(model_path):
        os.makedirs(model_path)

    if not os.path.exists(summary_path):
        os.makedirs(summary_path)

    optimizer_name = "Adam"
    lr = 0.001

    if load:
        model = wave_net.model
        model.load_weights(model_path + "/model.ckpt")
    else:
        model = wave_net.model

    if optimizer_name == "Adam":
        optimizer = Adam(lr=lr)
    elif optimizer_name == "AdaDelta":
        optimizer = Adadelta(lr=lr)
    else:
        optimizer = RMSprop(lr=lr)

    model.compile(loss=tf.keras.losses.BinaryCrossentropy(),
                  optimizer=optimizer,
                  metrics=[tf.keras.metrics.Accuracy(), tf.keras.metrics.Precision(), tf.keras.metrics.Recall()])


    checkpoint_cb = ModelCheckpoint(model_path + "/model.ckpt", save_weights_only=True, save_best_only=True)
    tensorboard_cb = TensorBoard(summary_path)
    early_stopping_cb = EarlyStopping(patience=2, restore_best_weights=True)

    history = model.fit((X_train_vol, X_train_sec), y_train, validation_split=0.15, epochs=10,
                        callbacks=[checkpoint_cb, tensorboard_cb, early_stopping_cb])

    loss, accuracy, precision, recall = model.evaluate((X_test_vol, X_test_sec), y_test)

    # model_path_tf = os.path.join(os.getcwd(), 'model_B', 'model')
    # model.save_weights(model_path_tf, save_format="tf")

    print(X_test_vol.shape)
    print(X_test_sec.shape)
    print(model.predict((X_test_vol, X_test_sec)).shape)
    print(loss, accuracy, precision, recall)
    model.summary()