# 改編自https://iter01.com/418571.html
from keras import regularizers
from keras import metrics
from keras import optimizers
import jieba
from keras.layers import BatchNormalization
from keras.callbacks import ReduceLROnPlateau
from keras.callbacks import EarlyStopping
from keras.callbacks import ModelCheckpoint
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from keras.layers import LSTM, Dense, Embedding, Dropout
from keras.preprocessing.sequence import pad_sequences
from keras.models import Sequential
from keras.utils import np_utils, plot_model
import pandas as pd
import numpy as np
import pickle
import os
os.environ["PATH"] += os.pathsep + 'C:/Program Files (x86)/Graphviz2.38/bin/'
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"

# 用cudnnlstm試試
# from keras.layers import CuDNNLSTM
# from tensorflow.python.compiler.tensorrt import trt_convert as trt
print("import good")



# 匯入資料
# 檔案的資料中，特徵為evaluation, 類別為label.


def load_data(filepath, input_shape, train_files_path):
    df = pd.read_csv(filepath)

    # 標籤及詞彙表
    labels, comments = list(df['label'].unique()), list(
        df['evaluation'].unique())
    # 構造字元級別的特徵
    words = []
    word_list = []
    comments_words_list = []
    for sentence in comments:
        words = jieba.cut(sentence, cut_all=False)
        for word in words:
            word_list.append(word)
    vocabulary = set(word_list)
    # vocabulary.add('模型沒看過的詞')

    # print(list(enumerate(labels)))

    # 字典列表
    # 在KERAS中 第0個別有用途 所以要從第1個開始放
    word_dictionary = {word: i+1 for i, word in enumerate(vocabulary)}

    word_dict_path=train_files_path+'_word_dict.pk'
    with open(word_dict_path, 'wb') as f:
        pickle.dump(word_dictionary, f)
    inverse_word_dictionary = {i+1: word for i, word in enumerate(vocabulary)}

    label_dictionary = {label: i for i, label in enumerate(labels)}

    label_dict_path=train_files_path+'_label_dict.pk'
    with open(label_dict_path, 'wb') as f:
        pickle.dump(label_dictionary, f)
    # print(label_dictionary)
    output_dictionary = {i: labels for i, labels in enumerate(labels)}

    vocab_size = len(word_dictionary.keys())  # 詞彙表大小
    label_size = len(label_dictionary.keys())  # 標籤類別數量
    print(vocab_size)

    # 序列填充，按input_shape填充，長度不足的按0補充

    x = [[word_dictionary[word] for word in jieba.cut(
        sent, cut_all=False)] for sent in df['evaluation']]
    x = pad_sequences(maxlen=input_shape, sequences=x, padding='post', value=0)
    y = [[label_dictionary[sent]] for sent in df['label']]
    y = [np_utils.to_categorical(label, num_classes=label_size) for label in y]
    y = np.array([list(_[0]) for _ in y])

    return x, y, output_dictionary, vocab_size, label_size, inverse_word_dictionary

# 建立深度學習模型， Embedding + LSTM + Softmax.


def create_LSTM(n_units, input_shape, output_dim, filepath, train_files_path):
    x, y, output_dictionary, vocab_size, label_size, inverse_word_dictionary = load_data(
        filepath, input_shape, train_files_path)
    model = Sequential()

    model.add(Embedding(input_dim=vocab_size + 1, output_dim=output_dim,
                        input_length=input_shape, mask_zero=True))

    # model.add(LSTM(n_units,kernel_regularizer=regularizers.l1(0.001), input_shape=(x.shape[0], x.shape[1])))
    # 業界朋友建議用用看BSLTM
    model.add(LSTM(n_units, input_shape=(x.shape[0], x.shape[1])))
    # model.add(LSTM(n_units, input_shape=(x.shape[0], x.shape[1]), return_sequences=True))
    # model.add(Dropout(0.5))
    # model.add(LSTM(n_units, return_sequences=False))
    #model.add(LSTM(n_units, return_sequences=False))
    #model.add(LSTM(n_units, return_sequences=False))
    # 用cudnnlstm試試
    # model.add(CuDNNLSTM(n_units, input_shape=(x.shape[0], x.shape[1])))
    # model.add(Dropout(0.1))
    # model.add(Dense(label_size, activation='relu'))
    #model.add(Dense(label_size, activation='relu'))
    #model.add(Dense(label_size, activation='relu'))
    #model.add(Dense(label_size, activation='relu'))
    # model.add(Dense(label_size, activation='softmax'))
    model.add(Dense(label_size, activation='sigmoid'))

    # model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
    # model.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
    # model.compile(loss='binary_crossentropy', optimizer=optimizers.RMSprop(lr=0.0003), metrics=[metrics.binary_accuracy])
    model.compile(loss='binary_crossentropy', optimizer=optimizers.RMSprop(
        lr=0.0003), metrics=['accuracy'])
    # model.compile(loss='binary_crossentropy', optimizer=optimizers.Adam(lr=0.0003), metrics=['accuracy'])

    model_plot_path= train_files_path+'_model_lstm.png'
    plot_model(model, to_file=model_plot_path, show_shapes=True)
    model.summary()

    return model


print("def create_LSTM good")


# 模型訓練
def model_train(input_shape, filepath, train_files_path):

    # 將資料集分為訓練集和測試集，佔比為9:1
    # input_shape = 100

    x, y, output_dictionary, vocab_size, label_size, inverse_word_dictionary = load_data(
        filepath, input_shape, train_files_path)
    train_x, test_x, train_y, test_y = train_test_split(
        x, y, test_size=0.1, random_state=42)

    # print(test_x)
    # print(test_y)

    # 模型輸入引數，需要自己根據需要調整
    # n_units 是 LSTM中神經元的數量
    n_units = 256
    # batch_size是學習時的資料批次數量
    batch_size = 256

    epochs = 200
    # embedding的輸出維度
    output_dim = 256

    # 模型訓練
    lstm_model = create_LSTM(n_units, input_shape, output_dim, filepath, train_files_path)

    model_save_path = train_files_path+'_corpus_model.h5'
    checkpointer = ModelCheckpoint(
        filepath=model_save_path, verbose=1, save_best_only=True, save_weights_only=True)
    earlystopping = EarlyStopping(
        monitor='val_loss', min_delta=0.01, patience=30, mode='auto')
    reduceLR = ReduceLROnPlateau(
        monitor='val_loss', factor=0.1, patience=10, mode='auto')

    history = lstm_model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size, verbose=1, validation_data=(
        test_x, test_y), callbacks=[checkpointer, earlystopping, reduceLR])
    # history=lstm_model.fit(train_x, train_y, epochs=epochs, batch_size=batch_size, verbose=1, validation_data=(test_x, test_y))

    print(history.history.keys())
    # 畫出訓練過程
    acc = history.history['accuracy']
    # acc=history.history['binary_accuracy']
    val_acc = history.history['val_accuracy']
    # val_acc=history.history['val_binary_accuracy']
    loss = history.history['loss']
    val_loss = history.history['val_loss']

    epo = range(1, len(acc)+1)

    plt.plot(epo, acc, 'bo', label='Training acc')
    plt.plot(epo, val_acc, 'r', label='Test acc')
    plt.title('Training and test accuracy')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.savefig(train_files_path+'_Accuracy.png')
    plt.figure()

    plt.plot(epo, loss, 'bo', label='Training loss')
    plt.plot(epo, val_loss, 'r', label='Test loss')
    plt.title('Training and test loss')
    plt.xlabel('Epochs')
    plt.ylabel('Loss')
    plt.legend()
    plt.savefig(train_files_path+'_Loss.png')
    plt.show()

    # 模型儲存
    lstm_model.save(model_save_path)
    model_weight_path=train_files_path+'_model.weight'
    lstm_model.save_weights(model_weight_path)

    N = test_x.shape[0]  # 測試的條數
    predict = []
    label = []
    for start, end in zip(range(0, N, 1), range(1, N+1, 1)):
        sentence = [inverse_word_dictionary[i]
                    for i in test_x[start] if i != 0]
        y_predict = lstm_model.predict(test_x[start:end])
        label_predict = output_dictionary[np.argmax(y_predict[0])]
        label_true = output_dictionary[np.argmax(test_y[start:end])]
        print(''.join(sentence), label_true, label_predict)  # 輸出預測結果
        predict.append(label_predict)
        label.append(label_true)

    acc = accuracy_score(predict, label)  # 預測準確率
    print('模型在測試集上的準確率為: %s.' % acc)
    # 畫TRANING與TESTING的LOSS及ACCURACY


print("def model_train good")


if __name__ == '__main__':
    # 先把要存檔的位置都指定好
    py_path = os.path.dirname(os.path.realpath(__file__)).replace("\\", '/')
    total_path=os.path.dirname(py_path)
    databaseName = 'food_comments_X28_2020_7_13_12_34'
    train_files_path=total_path+f'/{databaseName}/{databaseName}'
    # filepath = './5cities_pn_tv.csv'
    filepath = total_path+f'/{databaseName}/restaurant_comments_{databaseName}_all.csv'
    input_shape = 64
    print("model_train start")
    model_train(input_shape, filepath, train_files_path)

print("model_train good")
