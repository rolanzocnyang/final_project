import csv
import pandas as pd
from bs4 import BeautifulSoup as bs
import re
# from string import punctuation as punc_en
# from zhon.hanzi import punctuation as punc_ch
import pandas as pd
import matplotlib.pyplot as plt

def pre_pn(restaurants_qty, databaseName):
    # 輸入大安區 義大利麵抓到的店家總數
    # 要輸入實際有抓到評論的店家 所以這邊手動輸入一下
    # 有時候最後一個店家會出現沒有存到原始碼的現象 有空去爬蟲那邊釐清一下吧
    # restaurants_qty = 28
    # 輸入檔案名稱
    # 可以一次處裡一個資料夾的原始碼 所以也手動輸入資料夾名稱確認一下吧
    # databaseName = 'food_comments_X28_2020_7_13_12_34'

    # 新增一個CSV檔存這個資料夾裡所有有效評論(要經過資料平衡)
    restaurants_comments_all_csv = f'{databaseName}/restaurant_comments_{databaseName}_all.csv'
    with open(restaurants_comments_all_csv, 'w', newline='', encoding="utf-8") as csvfile:
        fieldnames_comments_all = ['evaluation', 'label']
        # 將 dictionary 寫入 CSV 檔
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames_comments_all)
        # 寫入第一列的欄位名稱
        writer.writeheader()

    # 一家一家來看
    for num in range(restaurants_qty):
        # 第1家的num是0
        collection_num = num+1
        # 這一個是用來存每家各自的評論 用來做單一店家的評論分析 不過要評論數夠多的店家才能做喔
        # 這邊不用經過資料平衡
        restaurants_comments_csv = f'{databaseName}/restaurant_comments_{collection_num}_{databaseName}_prepocessed.csv'
        # 先做個垂直的欄位標題
        with open(restaurants_comments_csv, 'w', newline='', encoding="utf-8") as csvfile:
            fieldnames_comments = ['_id', 'sid_comment', 'star', 'time',
                                "comment"]
            # 將 dictionary 寫入 CSV 檔
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames_comments)
            # 寫入第一列的欄位名稱
            writer.writeheader()

        # 拿出先前爬到的網頁原始碼 每家都有存 一次開一家
        comments_html = ''
        comments_html_raw_data = f'{databaseName}/restaurant_comments_{collection_num}_{databaseName}.txt'
        with open(comments_html_raw_data, 'r', newline='', encoding="utf-8") as txtfile:
            comments_html = txtfile.read()

        # 用BEAUTIFUL SOUP對原始碼做解析
        # LXML也要先灌好
        comments_soup = bs(comments_html, 'lxml')

        # 從解析完的原始碼中 抓到這家的所有評論 做成一個LIST
        try:
            comments_list = comments_soup.select(
                '[class="WMbnJf gws-localreviews__google-review"]')
        except:
            print("這個餐廳找不到評論 奇怪了 去網頁上看一下店家評論的狀況 或是看看爬到的原始碼有沒有問題")

        # 做個評論流水號
        sid_comment = 1
        # 算一下每一家有幾則有效評論
        effective_comments_qty = 0
        # 算一下每一家有幾則空評論
        null_comments_qty = 0
        # 算一下每一家正評數量 在資料平衡時計算用
        pos_comments_qty = 0
        # 針對其中一家 把她的評論一則一則來看
        for comment in comments_list:
            # 從每個評論中 抓出星級、全文及時間 存到DICT 再存到CSV裡 
            # 這三個如果在有評論的情況下沒有抓到 可能是網頁改版了
            # 這時候直接跳ERROR會比較好 再進來把切入點更新即可
            # 所以就不寫TRY跟EXCEPT啦
            # ~~~~~~~~~~~~~~~~
            # 這些CSV分別送給1.總評TFIDF前百大關鍵字、2.推薦排行榜、3.商業報告及4.深度學習模型
            # 其中總評TFIDF前百大關鍵字最為重要 幾乎決定了整個其他產品如何分類及呈現
            # 目前我的專案用18萬則評論平衡而成的3萬則評論總表來做
            # 這種做法還有待確認是否最佳 等有空再試試看
            # (比方說 換成用正評居多的18萬則直接取TFIDF是否能得到更多元的關鍵字及分類)
            # 深度學習的模型也是由3萬則評論總表來做
            # 而推薦排行榜及商業報告都是由各店家的評論生成
            # ~~~~~~~~~~~~~~~~
            # 以下三行註解是經驗談 因為曾經用LIST來裝迴圈中每一次產生的DICT 後來就用不到了 直接把每個DICT寫進CSV即可
            # 如果在迴圈外宣告這個DICT 就只會有一個記憶體位址 而LIST中每一項都會指到同一個位址
            # 當第二次迴圈時 複寫原本記憶體位址的DICT時 就會連同LIST中第一個DICT也一起被改到
            # 所以這個DICT一定要放在迴圈內! 不然產生的LIST裡的東西全都會一樣 沒有意義
            # ~~~~~~~~~~~~~~~~
            # 抓出星級(小心CLASS名稱會變 盡量找到比較不會變的切入點為佳)
            star_select = comment.select_one('[class="Fam1ne EBe2gf"]')
            star_select_num = str(star_select)[21:22].strip()
            # 抓出時間(小心CLASS名稱會變 盡量找到比較不會變的切入點為佳)
            time_select = comment.select_one(
                f'[class="dehysf"]').text
            # 抓出評論(一臉就不會變的CLASS名稱) 如果有全文SPAN就抓全文 如果沒有還是得抓
            if(comment.select_one('[class="review-full-text"]')):
                comment_select = comment.select_one(
                    '[class="review-full-text"]').text
            else:
                comment_select = comment.select_one(
                    '[jscontroller="P7L8k"]').text
            # ~~~~~~~每則評論的前處理開始
            # ---------------------1. 不要寫入評論是空白的資料 並跳出迴圈 繼續下一則評論
            # (通常評論少的店家 排在後面的評論都是空評論)
            if not comment_select:
                print(f"第{collection_num}家的第{sid_comment}條是空評論，不寫入")
                sid_comment += 1
                null_comments_qty += 1
                continue
            # ---------------------2. 如果評論中有出現"(由 Google 提供翻譯) " 把它刪掉
            comment_select = comment_select.replace('(由 Google 提供翻譯) ', '', 1)
            # ---------------------3. 如果評論中有出現"(原始評論)" 以它為中心將字串切成兩個 
            # 留下前面那個 才是被翻譯成中文的
            comment_select = comment_select.split('(原始評論)')[0]
            # ---------------------4. 把四五星的評價放到pos 把一二星的評價放到neg
            if star_select_num == '5' or star_select_num == '4':
                star_select_num = 'pos'
            if star_select_num == '1' or star_select_num == '2':
                star_select_num = 'neg'
            # # ---------------------5. 把評論中的標點符號拿掉(發現在情緒判別時某些標點符號有助於判別 先不拿掉)
            # 英文標點符號
            # comment_select=re.sub("[{}]+".format(punc_en), " ", comment_select)
            # 中文標點符號
            # comment_select=re.sub("[{}]+".format(punc_ch), " ", comment_select)
            # ~~~~~~~評論前處理結束
            print(f"第{collection_num}家的第{sid_comment}條評論前處理完成")
            effective_comments_qty += 1
            # 上傳到MONGODB各自的COLLECTION
            # food_comments = db[f'food_comments_{collection_num}_{restaurant_name}_{databaseName}']
            # 要送去做排行榜及商業報告的資料盡量完整 未來可做更細節的分析
            # 名稱的話...因為原本是打算上傳到資料庫啦
            to_mongo_dict = {"sid_comment": sid_comment, "star": star_select_num, "time": time_select,
                            "comment": comment_select}
            # 要送去做TFIDF及深度學習的資料只需要內文及標籤即可
            # (有空時可以改一下DL那邊 讓兩邊的資料可以共用)
            to_lstm_dict = {'evaluation': comment_select, 'label': star_select_num}
            # food_comments.insert(to_mongo_dict)
            # 存到個別餐廳的CSV 都是未經平衡的評論 也比較完整
            with open(restaurants_comments_csv, 'a', newline='', encoding="utf-8") as csvfile:
                # 宣告writer時還是要讀取fieldnames
                writer = csv.DictWriter(
                    csvfile, fieldnames=fieldnames_comments)
                # 這時就不用再寫一次head 而是直接寫row
                writer.writerow(to_mongo_dict)

            # 若不是正負評(三星) 就不寫入總表 並跳出迴圈 繼續下一則評論
                if (star_select_num != 'pos') & (star_select_num != 'neg'):
                    sid_comment += 1
                    continue
            # 如果是pos 10筆才寫入1筆 如果不是就跳出迴圈 繼續下一則評論
                if star_select_num == 'pos':
                    pos_comments_qty += 1
                    if (pos_comments_qty % 10) != 1:
                        sid_comment += 1
                        continue
            # 將這則評論寫入總表
            with open(restaurants_comments_all_csv, 'a', newline='', encoding="utf-8") as csvfile:
                # 宣告writer時還是要讀取fieldnames
                writer = csv.DictWriter(
                    csvfile, fieldnames=fieldnames_comments_all)
                # 這時就不用再寫一次head 而是直接寫row
                writer.writerow(to_lstm_dict)
            sid_comment += 1
        print(f'共寫入{effective_comments_qty}條有效評論')
        print(f'共移除掉{null_comments_qty}條空評論')
        # ````````````````````````````````` 回到餐廳列表
        print(f"處理完第{collection_num}家評論 換下一家")
    print("前處理完成")
    # 存一張長條圖出來 看看總表正負評論是否平衡
    # 把CSV資料拿出來
    df = pd.read_csv(restaurants_comments_all_csv)
    # 把每種LABEL具有的評論數量算出來
    df = df.groupby("label").size()
    # y就是各個LABEL具有的評論數 做成一個LIST
    y = list(df.values)
    # x就是各個LABEL名稱 做成一個LIST
    x = list(df.index)
    # 有兩個長度一樣的LIST 就可以畫長條圖 對應的X軸名稱及Y軸的值
    # 各自對應 做成長條圖 放在plt中
    plt.bar(x, y)
    # 存到指定路徑
    plt.savefig(f'{databaseName}/label.png')  # 儲存圖片
    # 秀出來
    plt.show()
    return 0

if __name__ == '__main__':
    # 範例目標：某個資料夾 爬到28家 資料夾名稱是'food_comments_X28_2020_7_13_12_34'
    pre_pn(28, 'food_comments_X28_2020_7_13_12_34')
    # 要再加上打亂以及產生tv&v的資料集