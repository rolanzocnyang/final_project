# 改編自https://iter01.com/418571.html
# Import the necessary modules
import pickle
import numpy as np
from keras.models import load_model
from keras.preprocessing.sequence import pad_sequences
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
import jieba
import pandas as pd

import seaborn as sns 
from sklearn.metrics import confusion_matrix 
import matplotlib.pyplot as plt


# 匯入字典
with open('word_dict.pk', 'rb') as f:
    word_dictionary = pickle.load(f)
with open('label_dict.pk', 'rb') as f:
    output_dictionary = pickle.load(f)

input_shape = 90
# 載入模型
# model_save_path = './sentiment_analysis.h5'
model_save_path = './corpus_model.h5'
lstm_model = load_model(model_save_path)

predict_star_list, label_star_list, tf_list=[], [], []
df = pd.read_csv('5cities_pn_t.csv')
for row_num in range(df.shape[0]):
    sent=df.loc[[row_num]]['evaluation'][row_num]
    print(sent)
    # try:
    # 資料預處理

    # sent = """
    # 亂七八糟
    # """


    words = jieba.cut(sent, cut_all=False)




    # x = [[word_dictionary[word] for word in words]]
    x = [word for word in words]


    for word_cut in x[0:]:
        # print(word_cut)
        # print(word_cut not in word_dictionary.keys())
        if  word_cut not in word_dictionary.keys():
            # print(f'字典裡沒有這個字:{word_cut}')
            x.remove(word_cut)

    x = [[word_dictionary[word] for word in x]]



    x = pad_sequences(maxlen=input_shape, sequences=x, padding='post', value=0)



    # 模型預測
    y_predict = lstm_model.predict(x)
    label_dict = {v:k for k,v in output_dictionary.items()}

    print('輸入語句: %s' % sent)
    print(f'情感預測結果: {label_dict[np.argmax(y_predict)]} 信心指數(機率):{y_predict[0][np.argmax(y_predict)]}')
# print(np.argmax(y_predict))
# print(label_dict)
# print(y_predict)

# except KeyError as err:
#     print("您輸入的句子有漢字不在詞彙表中，請重新輸入！")
#     print("不在詞彙表中的單詞為：%s." % err)
    predict_star=label_dict[np.argmax(y_predict)]
    label_star=df.loc[[row_num]]['label'][row_num]
    predict_star_list.append(predict_star)
    label_star_list.append(label_star)
    if label_star == predict_star:
        tf_list.append(True)
    else:
        tf_list.append(False)
df['predict'] = predict_star_list
df['label'] = label_star_list
df['T or F'] = tf_list
print((df['T or F'].sum())/df.shape[0])
print(pd.crosstab(df['label'],df['predict'],rownames=['label'],colnames=['predict']))
print(df['label'].shape)
print(df['predict'].shape)

sns.set() 
C2= confusion_matrix(list(df['label']), list(df['predict']), labels=["pos", "neg"]) 
print(C2)
sns.heatmap(C2,annot=True,fmt='.20g')
plt.savefig('./matrix.png')
plt.show()