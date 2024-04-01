# import 需要的套件
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import pandas as pd

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

data_order = ['hid','url','title','price','address','traffic']  #todo 調整資料在 json 呈現的順序 
data_limit = 10000  #todo 想要抓取的資料數量

data_list = []
page_pre = -1   #todo 偵測 page jump

def getdata(obj): #todo 傳入一整個 page 一次擷取多筆資料
    global data_limit
    pagedata = 0

    for i in obj:
        if data_limit <= 0:
            break
        
        data={}
        detail = i.find_element(By.CLASS_NAME, 'rent-item-right')   #todo bcz大部分資訊集中在某個區塊
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

    #todo 測試 page loading 是否完成
    while True:
        try:
            page_number = 
            break
        except Exception as e:
            print(f"An exception "{e}" occur")
            continue
    
    # page_number = WebDriverWait(driver, 10).until(
    #     EC.presence_of_element_located((By.CLASS_NAME, 'pageCurrent'))
    # )
    # page_number = int(page_number.text)
    # if page_pre == page_number:
    #     print('jump next page fails')
    #     break
    # page_pre = page_number

    #todo 往下滑
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    #todo 擷取 whole page
    obj = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'switch-list-content')) and
        EC.presence_of_all_elements_located((By.CLASS_NAME, 'vue-list-rent-item'))
    )

    getdata(obj)

    pagelimit = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'page-limit'))
    )

    try:    #todo Crawler over
        last_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.pageNext.last'))
        )
        print('Crawler over')
        break
    except Exception as e:  #todo nextpage
        nextpage = pagelimit.find_element(By.CLASS_NAME, 'pageNext')
        nextpage.click()

    page_pre = page_number

    #todo 等待跳頁
    time.sleep(3)

try:
    with open("D:/gold_house/data.json", "w", encoding="utf-8")as file:    #todo 存入 data.json 檔案
        json.dump(data_list, file, ensure_ascii=False, indent=4)
    print('json success')
except Exception as e:
    print('json fails')

try:
    df = pd.DataFrame(data_list)    #todo 存入 data.excel 檔案
    df.to_excel("D:/gold_house/data.xlsx", index=False, engine="openpyxl")
    print('excel success')
except Exception as e:
    print('excel fails')

print(f"共爬取: {len(data_list)} 筆資料")
time.sleep(10)
driver.quit()