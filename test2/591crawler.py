# import 需要的套件
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import pandas as pd
import time

# 編碼改為 utf-8
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 設置 driver 及 brower
path = "C:/Users/USER/Desktop/web_driver/chromedriver-win64/chromedriver.exe"
service = Service(path)
options = Options()
driver = webdriver.Chrome(service=service, options=options)

#做你想做的事
driver.get("https://rent.591.com.tw/?section=1,6,3,8,2&searchtype=1")

#! 可依使用者需求配置參數 (data_order), (data_limit), (loading_times)
data_order = ['hid','url','title','price','address','traffic']  #todo 調整資料在 json 呈現的順序 
data_limit = 10000  #todo 抓取資料的上限, 如果資料不足只能夠抓取盡量多的資料
loading_times = 50 #todo 等待新頁面加載的最大時間(second)

data_list = []
page_pre = -1

def getdata(obj): #todo 傳入一整個 page 一次擷取多筆資料
    global data_limit
    pagedata = 0

    for i in obj:
        if data_limit <= 0:
            break
        
        data={}
        detail = i.find_element(By.CLASS_NAME, 'rent-item-right')   #todo 大部分資訊集中在某個區塊
        url = i.find_element(By.TAG_NAME, 'a').get_attribute('href')
        title = detail.find_element(By.CLASS_NAME, 'item-title').text
        price = detail.find_element(By.CLASS_NAME, 'item-price-text').find_element(By.TAG_NAME, 'span').text
        price = int(price.replace(",", ""))
        traffic = detail.find_element(By.CLASS_NAME, 'item-tip').text
        address = detail.find_element(By.CLASS_NAME, 'item-area').text
        hid = i.get_attribute('data-bind')

        #! //資料篩選 (有些資料跟租屋沒關係)//
        del_data = detail.find_element(By.CLASS_NAME, 'item-style').find_element(By.CLASS_NAME, 'is-kind').text
        if del_data == "車位":
            print(f'give out {hid} data, title：{title}, price：{price}')
            continue
        
        #todo 儲存資料進 data_list
        data_order_mapping = {'url': url, 'title': title, 'price': price, 'address': address, 'traffic': traffic, 'hid':hid}
        data = {key: data_order_mapping[key] for key in data_order}
        data_list.append(data)
        pagedata += 1
        data_limit -= 1
    
    page_number = int(driver.find_element(By.CLASS_NAME, 'pageCurrent').text)
    print(f"page {page_number} 共取得：{pagedata} 筆資料")

while data_limit > 0:

    #todo 測試 page jump 是否成功
    loading_times_checking = loading_times   #todo 新頁面載入的時間上限
    while True:
        try:
            #todo 擷取當前 page number
            page_number = WebDriverWait(driver, 1).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'pageCurrent'))
            )
            page_number = int(page_number.text)

            if page_pre == page_number and loading_times_checking <= 0:
                data_limit = 0
                print(f"Crawler try to get {page_number+1} page {loading_times} times, but it failed")
            elif page_pre == page_number:
                loading_times_checking -= 1
                time.sleep(1)
                continue
            else:
                break
        except Exception as e:
            loading_times_checking -= 1
            time.sleep(1)
            continue

    #todo 往下滑
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    #todo 擷取 whole page
    obj = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'switch-list-content')) and
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'vue-list-rent-item'))
    )

    getdata(obj)
    page_pre = page_number

    try:    #todo Crawler over
        last_element = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.pageNext.last')) #todo 最後一頁有 last 標籤 
        )
        print('Crawler over')
        break
    except Exception as e:  #todo nextpage
        nextpage = driver.find_element(By.CLASS_NAME, 'page-limit').find_element(By.CLASS_NAME, 'pageNext')
        nextpage.click()

#todo 存入 data.json 檔案
try:
    with open("D:/gold_house/data.json", "w", encoding="utf-8")as file:
        json.dump(data_list, file, ensure_ascii=False, indent=4)
    print('json success')
except Exception as e:
    print('json fails')

#todo 存入 data.excel 檔案
try:
    df = pd.DataFrame(data_list)
    df.to_excel("D:/gold_house/data.xlsx", index=False, engine="openpyxl")
    print('excel success')
except Exception as e:
    print('excel fails')

print(f"共爬取: {len(data_list)} 筆資料")
time.sleep(10)
driver.quit()