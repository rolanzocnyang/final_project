import locale
import math
# 如果要把爬到的東西直接上傳到MONGODB 可以用pymongo
#from pymongo import Connection, errors
# 可用日期自動幫爬到的資料取名
import datetime
# 寫入CSV備份
import csv
# selenium常用的等待函式
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
# 強制停止的函式
from time import sleep
import pandas as pd
# bs解析爬到的網頁
from bs4 import BeautifulSoup as bs
# selenium的webdriver
from selenium import webdriver
# 爬蟲時使用鍵盤
from selenium.webdriver.common.keys import Keys
# 爬蟲時使用滑鼠滾輪
import pyautogui as pag
# TIMEOUT對策
from selenium.common.exceptions import TimeoutException
import os
# 指定CHROME DRIVER檔案路徑
import sys

# 用絕對路徑點擊元素的函數
def xpath_click(xpath_temp, browser, waiting_time):
    WebDriverWait(browser, waiting_time).until(
    EC.presence_of_all_elements_located((By.XPATH, xpath_temp)))
    browser.find_element_by_xpath(xpath_temp).click()

# 用CSS點擊元素的函數
def css_click(css_temp, browser, waiting_time):
    WebDriverWait(browser, waiting_time).until(EC.presence_of_all_elements_located(
    (By.CSS_SELECTOR, css_temp)))
    browser.find_element_by_css_selector(css_temp).click()

# 用絕對路徑抓文字內容的函數
def xpath_text(xpath_temp, browser, waiting_time):
    WebDriverWait(browser, waiting_time).until(EC.presence_of_all_elements_located(
        (By.XPATH, xpath_temp)))
    restaurant_name = browser.find_element_by_xpath(
        xpath_temp).text
    return restaurant_name

# 正式開始爬蟲的函數
def google_comments_crawler(search_string):
    pag.FAILSAFE = True
    # 在計算滑鼠要下拉到底幾次時 取CEILING用
    # 在美國/英國，逗號作為千位分隔符 所以要用這個來搞
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')

    # 調整CHROME的細節
    options = webdriver.ChromeOptions()
    # 不要顯示瀏覽器
    # options.add_argument('--headless')
    # 使用無痕模式
    options.add_argument("--incognito")

    print("start crawler")
    # 有需要的話可以用REQUEST 比方說沒有使用JS的網站
    # import requests as re
    # s=re.Session()

    # 要爬的網址
    URL = 'https://www.google.com.tw'
    # 用SELENIUM打開CHROME
    # 記得檢查chromedriver有沒有更新
    # https://chromedriver.chromium.org/downloads
    # chromedriver放在同一資料夾
    browser = webdriver.Chrome(
        executable_path=sys.path[0]+'/chromedriver83',
        options=options)  
    # 然後去google網址
    browser.get(URL)
    # 找到Google 搜尋的INPUT元素
    try:
        WebDriverWait(browser, 1).until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '[title="Google 搜尋"]')))
    except:
        print("連GOOGLE首頁都開不起來 網路是不是有問題")
    # 輸入要搜尋的字串
    browser.find_element_by_css_selector('[title="Google 搜尋"]').send_keys(
        search_string)
    # 按ENTER
    browser.find_element_by_css_selector(
        '[title="Google 搜尋"]').send_keys(Keys.ENTER)
    # 點選"更多地點"(GOOGLE有時會跳出第二種版本的按鈕)

    #停個5秒 有一陣子GOOGLE會在此時跳出阻擋機器人的網頁 如果遇到就來這邊把秒數設個60秒 手動解掉再進去
    # 未來展望當然就是用圖像辨識來搞這段啦   
    sleep(5)

    # 按'更多地點'
    try:
        xpath_temp = '//*[@id="rso"]/div[1]/div/div[2]/div/div[4]/div[3]/div/div/a'
        xpath_click(xpath_temp, browser, 1)
    except:
        try:
            xpath_temp = '//*[@id="rso"]/div[1]/div/div[2]/div/div[4]/div[3]/div/g-more-link/a'
            xpath_click(xpath_temp, browser, 1)
        except:
            print("抓不到 更多地點 按鈕")
    # 來到餐廳列表 假設有6頁
    # 先宣告要存的collection號碼 要存大概120家(一頁最多20家)
    # 從第一頁餐廳列表開始
    page = 1
    # 從第一家開始
    collection_num = 1
    # 找出餐廳列表總數
    page_total = 1
    # 找出所有剩下餐廳列表網址 然後逐個產生新分頁(2~5頁都開)
    while True:
        try:
            css_temp = f'[aria-label="Page {page_total+1}"]'
            # 找不到下一分頁時 在此跳出迴圈
            WebDriverWait(browser, 1).until(EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, css_temp)))
            page_href = browser.find_element_by_css_selector(
                css_temp).get_attribute('href')
            js = f'window.open("{page_href}");'
            browser.execute_script(js)
            page_total += 1
        except TimeoutException:
            print(f"有{page_total}頁餐廳列表")
            break

    # 產生所有分頁後 先切回到第1分頁
    page_tag = 0
    browser.switch_to.window(browser.window_handles[page_tag])


    # 先算一下一共要抓到幾間餐廳的評論
    # 大概抓一下而已 爬蟲過程中常出事
    restaurants_total = 0
    element_per_page = 0
    element_per_page_list = []

    # 所有頁數一頁一頁翻
    for page_for in range(page_total):
        # 每頁餐廳一家一家算
        while True:
            try:
                # google餐廳列表從1開始
                # 因為每頁最後一次會找不到才去except 所以每一FOR迴圈必定要等至少1秒
                xpath_temp = f'//*[@id="rl_ist0"]/div[1]/div[4]/div[{element_per_page+1}]/div'
                WebDriverWait(browser, 1).until(EC.presence_of_all_elements_located(
                    (By.XPATH, xpath_temp)))
                browser.find_element_by_xpath(xpath_temp)
                element_per_page += 1
            except:
                if (page_for+1 == 1):
                    # 第一頁要經過第6個廣告 但不要經過第22個
                    element_per_page_list.append(
                        element_per_page-1)
                    restaurants_total += element_per_page_list[page_for]-1
                    print(
                        f"第{page_for+1}頁有{element_per_page_list[page_for]-1}家餐廳，第6&{element_per_page}個是廣告")
                    element_per_page = 0
                    page_tag += -1
                    browser.switch_to.window(browser.window_handles[page_tag])
                    break
                elif (page_for+1 == page_total):
                    # 最後一頁不經過廣告
                    element_per_page_list.append(element_per_page)
                    restaurants_total += element_per_page_list[page_for]
                    print(
                        f"第{page_for+1}頁有{element_per_page_list[page_for]}家餐廳，最後一頁沒有廣告")
                    element_per_page = 0
                    page_tag += -1
                    browser.switch_to.window(browser.window_handles[page_tag])
                    break
                else:
                    # 其他頁不要經過第21個
                    element_per_page_list.append(
                        element_per_page-1)
                    restaurants_total += element_per_page_list[page_for]
                    print(
                        f"第{page_for+1}頁有{element_per_page_list[page_for]}家餐廳，第{element_per_page}個是廣告")
                    element_per_page = 0
                    page_tag += -1
                    browser.switch_to.window(browser.window_handles[page_tag])
                    break


    print(f"一共要爬{restaurants_total}間餐廳")
    print("所有元素如下")
    print(element_per_page_list)

    # 自動再次回到第1分頁
    page_tag = 0
    browser.switch_to.window(browser.window_handles[page_tag])
    sleep(1)


    # 自訂的DB名稱
    # 讓DB及文件自動照時間命名 以免忘記改
    today = datetime.datetime.now()
    databaseName = f"food_comments_X{restaurants_total}_{today.year}_{today.month}_{today.day}_{today.hour}_{today.minute}"

    # 連上MONGODB
    # connection = Connection()
    # try:
    #     # 注意!!! 每次重抓都會刪掉DATABASE 如果要改名備份要在程式開始之前完成
    #     connection.drop_database(databaseName)
    #     print("已刪除database")
    # except errors.OperationFailure as err:
    #     # 就算MONGODB上面沒有這個database好像也不會出問題 保險起見還是寫一下
    #     print("PyMongo ERROR:", err, "\n")
    # db = connection[databaseName]
    # # 記得另外開一個TERMINAL 啟動MONGODB
    # # cd C:\Program Files\MongoDB\Server\4.2\bin

    # 開個新資料夾
    path_dir = f"{databaseName}"
    if not os.path.isdir(path_dir):
        os.mkdir(path_dir)

    # 準備寫入餐廳資訊的CSV檔 用w+建立
    restaurants_info_csv = f'restaurant_info_{databaseName}.csv'
    with open(path_dir + "\\" + restaurants_info_csv, 'w', newline='', encoding="utf-8") as csvfile:
        fieldnames_info = ['_id', '餐廳編號', '餐廳名稱', '餐廳星級',
                        "餐廳評論數量", "餐廳價格等級", "餐廳類型", "餐廳特色", "餐廳地址"]
        # 將 dictionary 寫入 CSV 檔
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames_info)
        # 寫入第一列的欄位名稱
        writer.writeheader()


    # 正式開爬

    # 看有幾頁餐廳列表就跑幾次 目前有六頁(分頁) 就跑六次 每爬完一分頁就去下一分頁
    for _ in range(page_total):

        # 秀出每頁有幾個餐廳

        if (page == 1):
            print(
                f"開始爬第{page}頁餐廳列表，本頁有{element_per_page_list[page-1]-1}家餐廳")

        elif (page == page_total):
            print(
                f"開始爬第{page}頁餐廳列表，本頁有{element_per_page_list[page-1]}家餐廳")

        else:
            print(
                f"開始爬第{page}頁餐廳列表，本頁有{element_per_page_list[page-1]}家餐廳")

        for i in range(element_per_page_list[page-1]):

            # 一個一個 點選每一家餐廳
            # 如果點完餐廳了 就去下一頁餐廳列表
            # 如果是廣告(固定第一頁第六個)就跳過 去下一家餐廳
            if ((page == 1) & (i == 5)) or ((page == 1) & (i == 21)) or ((page != 1) & (i == 21)):
                print("跳過廣告")
                continue
            # 廣告會在這邊跳出回圈 其他繼續做事
            try:
                # GOOGLE在第二分頁開始 點擊第一家餐廳後回餐廳列表 會直接跳回第一頁餐廳列表
                # 所以跳回第一頁之後 要再跳去正確的頁數
                # 這個動作在爬第一頁 及 爬其他頁的第一個餐廳 都不用做
                if ((page != 1) & (i != 0)):
                    try:
                        css_temp = f'[aria-label="Page {page}"]'
                        css_click(css_temp, browser, 2)
                    except:
                        print("已在正確餐廳列表")

                # 點擊餐廳
                # 注意 這邊有時會怪怪 繼續觀察
                xpath_temp = f'//*[@id="rl_ist0"]/div[1]/div[4]/div[{i+1}]/div'
                xpath_click(xpath_temp, browser, 1)
                print(f"點擊第{collection_num}家餐廳----------------")
                sleep(1)
            except:
                print(f"第{page}頁的餐廳找完了")
                continue
                # 餐廳抓完 跳出回圈

            # 餐廳名稱
            # 餐廳名稱會可能有兩種路徑

            try:
                xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[1]/div/div[1]/div/div[2]/h2/span'
                restaurant_name=xpath_text(xpath_temp, browser, 1)
            except:
                try:
                    xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[1]/div/div[1]/div/div[1]/h2/span'
                    restaurant_name=xpath_text(xpath_temp, browser, 1)
                except:
                    restaurant_name = '沒有標示餐廳名稱'
            # 餐廳星級
            try:
                xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/div/span[1]'
                restaurant_star=xpath_text(xpath_temp, browser, 1)
            except:
                restaurant_star = '沒有標示餐廳星級'
            # 餐廳評論數量
            try:
                xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[1]/div/div[2]/div[1]/div/div/span[2]/span/a/span'
                restaurant_comments_qty=xpath_text(xpath_temp, browser, 1)
            except:
                restaurant_comments_qty = '沒有標示餐廳評論數量'
            # 餐廳價格等級 和 餐廳類型
            try:
                xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[1]/div/div[2]/div[2]/div/span[1]'
                restaurant_lv=xpath_text(xpath_temp, browser, 1)
            except:
                restaurant_lv = '沒有標示價格等級(路徑中沒東西)'
                # 餐廳可能沒有標示價格等級 這時要做替換 因為原本"餐廳價格等級"路徑存的是"餐廳類型"
            if not '$' in restaurant_lv:
                restaurant_type = restaurant_lv
                restaurant_lv = "沒有標示價格等級"
            else:
                try:
                    xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[1]/div/div[2]/div[2]/div/span[2]'
                    restaurant_type=xpath_text(xpath_temp, browser, 1)
                except:
                    restaurant_type = "沒有標示餐廳類型"
            # 餐廳特色
            # 餐廳特色會可能有兩種路徑 也可能沒有餐廳特色
            try:
                xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[3]/div/div[1]/c-wiz/div/div/div'
                restaurant_char=xpath_text(xpath_temp, browser, 1)    
            except:
                try:
                    xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[4]/div/div[1]/c-wiz/div/div/div'
                    restaurant_char=xpath_text(xpath_temp, browser, 1)   
                except:
                    restaurant_char = "沒有標示餐廳特色"
            try:
                xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[3]/div/div[3]/div/div/span[2]'
                restaurant_addr=xpath_text(xpath_temp, browser, 1)
            except:
                try:
                    xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[5]/div/div/span[2]'
                    restaurant_addr=xpath_text(xpath_temp, browser, 1)
                except:
                    try:
                        xpath_temp = '//*[@class="immersive-container"]/div[1]/div/div/div/div[1]/div/div[1]/div/div[4]/div/div[3]/div/div/span[2]'
                        restaurant_addr=xpath_text(xpath_temp, browser, 1)
                    except:
                        restaurant_addr = "沒有標示餐廳地址"


            restaurant_info_dict = {
                "餐廳編號": collection_num,
                "餐廳名稱": restaurant_name,
                "餐廳星級": restaurant_star,
                "餐廳評論數量": restaurant_comments_qty,
                "餐廳價格等級": restaurant_lv,
                "餐廳類型": restaurant_type,
                "餐廳特色": restaurant_char,
                "餐廳地址": restaurant_addr
            }
            print(restaurant_info_dict)
            # 上傳到餐廳資訊的COLLECTION
            # restaurant_info = db[f'restaurant_info_X{restaurants_total}_{databaseName}']
            # restaurant_info.insert(restaurant_info_dict)
            # 寫入餐廳資料到CSV 用a+附加上去
            # 準備寫入餐廳資訊的CSV檔 用w+建立
            # 注意!!!寫head跟寫row的檔名必須一模一樣 不然會寫到不同檔案
            # 特別用變數來控制
            with open(path_dir + "\\" + restaurants_info_csv, 'a', newline='', encoding="utf-8") as csvfile:
                # 宣告writer時還是要讀取fieldnames
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames_info)
                # 這時就不用再寫一次head 而是直接寫row
                writer.writerow(restaurant_info_dict)

        # 點選評論
            try:
                css_temp = '[data-async-trigger="reviewDialog"]'
                css_click(css_temp, browser, 1)
                print("點擊評論按鈕")
                # 等開始抓評論時要拿掉
                sleep(1)
            except:
                print("沒找到評論按鈕 先換下一家")
                continue
            # `````````````````````````````````終於成功到達評論頁面啦

            # 控制滑鼠移動到(500, 500)
            pag.moveTo(500, 500)
            # 找到這個餐廳的評論數
            num_eu = restaurant_info_dict["餐廳評論數量"].replace(' 則 Google 評論', '')
            try:
                # 注意! 因為評論數從GOOGLEMAP上爬下來時 資料格式是像"8,457 則 Google 評論"
                # 8,457是英美國家的計數方式 不能直接把此字串轉成INT 所以要用locale.atoi轉成INT
                # 在FOR迴圈外加上locale.setlocale(locale.LC_ALL, 'en_US.UTF-8') 才能使用下列指令
                comments_qty_num = locale.atoi(num_eu)
            except:
                xpath_temp = '//*[@style="display:inline-block"]/div/span'
                restaurant_comments_qty = xpath_text(xpath_temp, browser, 1)
                num_eu = restaurant_comments_qty.replace(' 則評論', '')

            # 控制滑鼠下滑 如果要抓三百筆 就要下滑29次 下滑一次可以抓到10筆
            # 如果要抓212筆 就要下滑CEILING((212-10)/10) = 21次
            for slide in range(math.ceil((comments_qty_num-10)/10)):
                pag.scroll(-5000)
                if slide > 150:
                    continue
                sleep(1)

            # 拿到評論列表網頁原始碼
            comments_html = browser.page_source
            comments_html_raw_data = f'restaurant_comments_{collection_num}_{databaseName}.txt'
            with open(path_dir + "\\" + comments_html_raw_data, 'w', newline='', encoding="utf-8") as txtfile:
                txtfile.write(comments_html)

            # ````````````````````````````````` 回到餐廳列表
            print(f"爬完第{collection_num}家評論 換下一家")
            browser.back()
            browser.back()
            collection_num += 1
        # 換下一頁(分頁)餐廳列表
        page += 1
        # 分頁的跳法要用減的
        page_tag += -1
        browser.switch_to.window(browser.window_handles[page_tag])

    print("所有餐廳都抓完了")
    sleep(60)
    # 關閉瀏覽器
    browser.quit()
    return 0

if __name__ == '__main__':
    # 範例目標：google 搜尋 "大安區 義大利麵"
    google_comments_crawler('花蓮 麻糬')
