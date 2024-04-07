# import 需要的套件
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
import json
import os

#todo 編碼改為 utf-8
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

#todo 設置 driver 及 brower
path = "C:/Users/USER/Desktop/web_driver/chromedriver-win64/chromedriver.exe"
service = Service(path)
options = Options()
driver = webdriver.Chrome(service=service, options=options)

#todo 載入 data.json
with open('data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

#! 可依使用者需求配置參數 (file_mode), (start_with_hid)
folder_mode = False   #todo False：檔案覆寫, True：檔案不覆寫
start_with_hid = '16327982'  #todo 0:表示從頭開始, [hid]:在掃到該筆資料前, 會全部捨棄

#todo 獲取某個物件下的所有 img url
def get_url(obj):
    wait = 0
    url = []
    for i in obj:
        while True: #todo 向下滑
            if i.get_attribute('src') == 'https://images.591.com.tw/index/house/newVersion/newload.gif':    #todo 未載入
                wait += 1
                if wait%100 == 0: #todo 太久沒有取得 url, 會從頭掃一次
                    time.sleep(1)
                    try:
                        ActionChains(driver).scroll_to_element(obj[0]).perform()    #todo 回到第一個元素
                    except:
                        ActionChains(driver).scroll_by_amount(0,-1000).perform()
                    
                ActionChains(driver).scroll_by_amount(0, 100).perform()

                #todo 如果完全找不到元素, reflesh 頁面
                # if wait >= 1500:
                #     driver.refresh()
                #     time.sleep(5)
                #     wait = 0
                #     url = get_url(obj)
                #     break
                # continue
            else:
                url.append(i.get_attribute('src'))
                break
    return url

lock = True
#todo 做你想做的事
for item in data:

    #todo 從指定 hid 開始爬取資料, 前面的資料則全部跳過
    if lock:
        if start_with_hid == 0:
            lock = False
        elif start_with_hid == item['hid']:
            print(f"Match {item['hid']}, title：{item['title']}")
            lock = False
        else:
            continue

    driver.get(item['url'])

    #todo 請求過快處理
    try:
        error = driver.find_element(By.TAG_NAME, 'body').text
        if error == "請求過快，請重試！":
            print('正在處理請求過快...\n')
            time.sleep(10)
            diver.reflesh()
    except:
        pass

    #todo 查看物件是否被刪除
    try:
        error = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, 'error-page'))
        )
        print(f"Item {item['hid']} with url：{item['url']}, title {item['title']} does not exists\n")
        time.sleep(1)
        continue
    except:
        pass

    #todo 創建資料夾
    folder_url = f"D:/gold_house/{item['hid']}"
    if not os.path.exists(folder_url):  #todo folder 是否存在
        os.makedirs(f"D:/gold_house/{item['hid']}")
        print(f"Success create folder {item['hid']}")
    else:
        print(f"Folder with item {item['hid']} already exists")
        if folder_mode == True:   #todo folder 已存在, 不執行覆寫
            print("No overlap, jump to next data\n")
            continue
        else:
            print("Start folder overlap")   #todo folder 已存在, 執行覆寫

    #todo 爬取照片數量, 原始頁面最多顯示 5 張照片, 其餘要跳轉頁面才能載入其他照片
    photo_list = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.photo-list.clearfix'))
    ).find_elements(By.TAG_NAME, 'img')
    if len(photo_list) <= 5:
        photo_list = driver.find_element(By.CSS_SELECTOR, '.house-images-list.clearfix').find_elements(By.TAG_NAME, 'img')
        src_list = get_url(photo_list)
    else:
        button = driver.find_element(By.CSS_SELECTOR, '.view-more.grey-btn')
        try:    #todo 一般 click() / 模擬滑鼠點擊
            button.click()
        except:
            ActionChains(driver).move_to_element(button).click().perform()
        src_list = get_url(photo_list)

    #todo 下載圖片
    number = 0
    for img in src_list:
        number += 1
        response = requests.get(img)
        if response.status_code == 200:
            image_path = os.path.join(folder_url, f"image{number}.jpg")
            with open(image_path, 'wb') as folder:
                folder.write(response.content)

    print(f"Success download {len(src_list)} photos to folder {item['hid']}\n")
    time.sleep(1)

time.sleep(10)
driver.quit()