# 改編自https://iter01.com/418571.html
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import font_manager
from itertools import accumulate
import os
import jieba

def get_input_shape(databaseName):
    # 此PY檔所在的目錄
    py_path = os.path.dirname(os.path.realpath(__file__)).replace("\\", '/')

    # 設定matplotlib繪圖時的字型
    my_font = font_manager.FontProperties(fname=py_path+"/Library/Fonts/GenSenRounded-B.ttc")

    # 統計句子長度及長度出現的頻數
    # 回上一層
    total_path=os.path.dirname(py_path)
    # 去目標資料夾 拿要用的總評CSV
    df = pd.read_csv(
        total_path+f'/{databaseName}/restaurant_comments_{databaseName}_all.csv')
    print('csv中的資料正負評數量如下')
    # 算一下正負評的數量
    # 複習一下 groupby就是把括弧中的欄位(COLUMN)名稱當作INDEX(ROW)的名稱 做成一個SeriesGroupBy
    # 這個SeriesGroupBy可以用下面這種方式算出該欄位中不同類分別有多少個 變成一個SERIES
    # print(df.groupby('label')['label'].count())
    # 其實用size()就可以啦 用timeit算完差不多快
    print(df.groupby('label').size())

    # 新增一欄叫length 內容是把evaluation欄位的的資料放進一個自訂函數後
    # 把函數輸出的結果做成一個SERIES
    # Lambda函數在資策會講義的第15-3頁
    # 簡單來說 輸入是x 輸出是len(x)
    # 而在這邊這個x就是evaluation欄位的每一項評論 所以會輸出每一個評論的'字數'
    # df['length'] = df['evaluation'].apply(lambda x: len(x))
    # 原本的程式碼沒有分詞 90%的評論字數大約在90以下
    # 加上分詞後 90%的詞數大約在56以下 這代表訓練可以用更快的時間完成
    df['length'] = df['evaluation'].apply(lambda x: len([word for word in jieba.cut(x, cut_all=False)]))
    # 然後 再把length欄位GROUPBY出來 count()算出每種詞數具有的評論數量 做成一個DataFrame
    # 在此例中 評論中最多詞數有到445
    len_df = df.groupby('length').count()
    # 把這個DataFrame的INDEX(ROW)抓出來做成LIST
    sent_length = len_df.index.tolist()
    # 同時 把這個DataFrame的評論欄位抓出來做成LIST
    # 要注意的是 此時的評論欄位顯示的是'每種詞數各有多少評論'
    sent_freq = len_df['evaluation'].tolist()

    # 繪製句子長度及出現頻數統計圖
    plt.bar(sent_length, sent_freq)
    # 出現在圖表上方的標題
    plt.title("句子長度及出現頻數統計圖", fontproperties=my_font)
    # X軸標題
    plt.xlabel("句子長度", fontproperties=my_font)
    # Y軸標題
    plt.ylabel("句子長度出現的頻數", fontproperties=my_font)
    plt.savefig(total_path+f"/{databaseName}/句子長度及出現頻數統計圖{databaseName}.png")
    # 如果要畫下一張圖 記得要把plt關掉
    plt.close()

    # 繪製句子長度累積分佈函式(CDF)
    # 複習一下 accumulate就是累加的意思 所以這邊是要把sent_freq這個LIST裡的數字
    # 第一個累加到第二個 再累加到第三個 依此類推 做成一個LIST
    # 接著 把累加後的LIST每一項取出來 除以原本sent_freq加總(像是累加比例 越來越接近1) 再做成一個LIST
    sent_pentage_list = [(count/sum(sent_freq)) for count in accumulate(sent_freq)]

    # 尋找分位點為quantile的句子長度
    # 也就是90%的評論都在此長度以下
    quantile = 0.90
    # ZIP會把兩個相同長度的LIST 其中的元素一個對一個形成TUPLE 所有TUPLE做成一個相同長度的LIST
    # 這邊的length, per分別對應到這個LIST中每一TUPLE的第0項及第1項
    for length, per in zip(sent_length, sent_pentage_list):
        # 複習一下 round是四捨五入 這邊是取到小數後第二位
        # 一但累加超過九成 就存下該種評論詞數 然後終止迴圈
        if round(per, 2) >= quantile:
            index = length
            break
    print(f"分位點為{quantile}的句子長度:{index}")

    # 繪製句子長度累積分佈函式圖CDF
    # plot畫出來會像是個連續的函數圖 每個X去對應到Y的點 連成曲線
    # 而這邊的Y就是每種詞數的評論數累加值 自然就形成累加圖摟
    plt.plot(sent_length, sent_pentage_list)
    # 畫一條垂直線 從y的起點到終點 及x的位置 水平線則反之 顏色的c代表cyan青色
    plt.hlines(quantile, 0, index, colors="c", linestyles="dashed")
    plt.vlines(index, 0, quantile, colors="c", linestyles="dashed")
    # 加上文字 x位置 y位置 文字內容
    plt.text(0, quantile, str(quantile))
    plt.text(index, 0, str(index))
    plt.title("句子長度累積分佈函式圖", fontproperties=my_font)
    plt.xlabel("句子長度", fontproperties=my_font)
    plt.ylabel("句子長度累積頻率", fontproperties=my_font)
    plt.savefig(total_path+f"/{databaseName}/句子長度累積分佈函式圖{databaseName}.png")
    plt.close()
    return 0

if __name__ == '__main__':
    # 範例目標：資料夾名稱是'food_comments_X28_2020_7_13_12_34'
    get_input_shape('food_comments_X28_2020_7_13_12_34')