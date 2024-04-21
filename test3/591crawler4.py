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
import sys

#* 編碼改為 utf-8
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

#* 設置 driver 及 brower
path = "C:/Users/USER/Desktop/web_driver/chromedriver-win64/chromedriver.exe"
service = Service(path)
options = Options()
driver = webdriver.Chrome(service=service, options=options)

#todo 路徑配置(需要手動配置)
file_path = 'detail.json' #! detail json 存取路徑
photo_path = 'D:/gold_house/info' #! 照片的存取路徑(用 hid 命名資料夾進行分類)
source_path = 'data.json' #! 來源資料

#todo 前置作業
#* 載入 data.json
with open(source_path, 'r', encoding='utf-8') as file:
    origin_data = json.load(file)

#* 檢查 json 所有物件 hid 是否唯一
check_set = set()
for item in origin_data:
    if item['hid'] in check_set:
        print('Data duplicated occur in data.json')
        sys.exit()
    check_set.add(item['hid'])

datalist = []

#* 檢查 detail.json 是否存在
#* 創建該資料夾, 將其餘資訊加入檔案
if not os.path.exists(file_path):
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump([], file, ensure_ascii=False, indent=4)
        print('Success create JSON file for detail information.')
else:
    with open(file_path, 'r', encoding='utf-8') as file:    #* 讀取 detail.json
        datalist = json.load(file)
    print('JSON file already exists, keep data crwaling.')

#* 紀錄上一次爬取成功的資料, 跳過先前爬取過的資料
if not datalist == []:
    pre_hid = datalist[-1]['hid']
else:
    pre_hid = 0

#todo 檢查資料存在和網頁處理(function)-----------
#* 處理請求過快
def check_request_success(driver):
    while True:
        try:
            error = driver.find_element(By.TAG_NAME, 'body').text
            if error == "請求過快，請重試！":
                print('正在處理請求過快...\n')
                time.sleep(10)
                driver.refresh()
                continue
            else:
                break
        except:
            time.sleep(1)
            continue

#* 處理物件不存在
def data_exist(driver, item):
    try:
        error = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, 'error-page'))
        )
        print(f"Item {item['hid']} with url：{item['url']}, title {item['title']} does not exists\n")
        time.sleep(1)
        return True
    except:
        return False

#todo 資料爬蟲區(function)------------
#* houseinfo
def get_houseinfo(obj):
    title = obj.find_element(By.CLASS_NAME, 'house-title').find_element(By.TAG_NAME, 'h1').text
    housepattern = obj.find_element(By.CLASS_NAME, 'house-pattern').find_elements(By.TAG_NAME, 'span')
    pattern = housepattern[0].text
    size = housepattern[2].text
    layer = housepattern[4].text
    types = housepattern[6].text
    price = obj.find_element(By.CLASS_NAME, 'house-price').find_element(By.TAG_NAME, 'b').text
    price = int(price.replace(",", ""))
    deposit = obj.find_element(By.CLASS_NAME, 'house-price').text

    #* 擷取預繳押金
    index_deposit = deposit.find("押金")
    if index_deposit != -1:
        index_month = deposit.find("月", index_deposit)
    
        if index_month != -1:  # 如果找到 "個月" 這個字串
            deposit = deposit[index_deposit:index_month + 1]  # 提取 "押金" 到 "個月" 這部分字串
    else:
        deposit = ""

    data = {
        'title':title,
        'pattern':pattern,
        'size':size,
        'layer':layer,
        'type':types,
        'price':price,
        'deposit':deposit
    }
    return data
    
#* positionRound
def get_position_round(obj):
    address = obj.find_element(By.CLASS_NAME, 'load-map').text
    subway = [elem.text.replace("\n","") for elem in obj.find_elements(By.CLASS_NAME, 'icon-subway')]
    bus = [elem.text.replace("\n","") for elem in obj.find_elements(By.CLASS_NAME, 'icon-bus')]
    
    data = {
        'address':address,
        'subway':subway,
        'bus':bus
    }
    return data

#* servicelist
def get_servicelist(obj):
    data = []
    service_items = obj.find_elements(By.CLASS_NAME, 'service-list-item')
    for item in service_items:
        avaliable = True
        device = item.find_element(By.CLASS_NAME, 'text').text
        if 'del' in item.get_attribute('class'):
            avaliable = False
        data.append(
            {
            'device':device,
            'avaliable':avaliable
            }
        )
    return data

#* remark
def get_remark(obj, hid):
    #* 爬取仲介資訊
    info = obj.find_element(By.CSS_SELECTOR, '.base-info.clearfix').find_element(By.CLASS_NAME, 'info').find_elements(By.TAG_NAME, 'p')
    agency = info[0].text.replace("仲介:", "")
    agency_company = info[1].find_element(By.TAG_NAME, 'span').text.replace("經紀業:","")

    #* 爬取仲介照片
    folder_url = f"{photo_path}/{hid}"
    if not os.path.exists(folder_url):
        os.makedirs(folder_url)
        print(f"Success create folder {hid}")
    else:
        print(f"Folder with item {hid} already exists")
    src = obj.find_element(By.CLASS_NAME, 'avatar').find_element(By.CLASS_NAME, 'reference').find_element(By.TAG_NAME, 'img').get_attribute('src')
    if not src == "https://images.591.com.tw/index/medium/no-photo-new.png":
        response = requests.get(src)
        if response.status_code == 200:
            image_path = os.path.join(folder_url, "agency.jpg")
            with open(image_path, 'wb') as folder:
                folder.write(response.content)
        else:
            print("Agency photo download failed")
    else:
        print("No agency photo")


    #* 爬取介紹文, 使用串列逐行爬取
    article = obj.find_element(By.CLASS_NAME, 'article').text
    content = [paragraph.strip() for paragraph in article.split('\n') if paragraph.strip()]

    data = {
        'agency':agency,
        'agency_company':agency_company,
        'content':content
    }

    return data

#* housedetail
def get_housedetail(obj):
    data = []
    left = obj.find_element(By.CLASS_NAME, 'main-info-left').find_element(By.CLASS_NAME, 'content').find_elements(By.XPATH, "./div")
    right = obj.find_element(By.CLASS_NAME, 'main-info-right').find_element(By.CLASS_NAME, 'content').find_elements(By.XPATH, "./div")
    for i in left:
        name = i.find_element(By.CLASS_NAME, 'name').text
        text = i.find_element(By.CLASS_NAME, 'text').text
        data.append({'name':name, 'text':text})
    for i in right:
        name = i.find_element(By.CLASS_NAME, 'name').text
        text = i.find_element(By.CLASS_NAME, 'text').text
        data.append(
            {
                'name':name,
                'text':text
            }
        )

    return data

#* near
def get_near(obj, hid):
    data = []
    near = obj.find_elements(By.CLASS_NAME, 'item-li')
    for item in near:
        #* 爬取附近房屋資料
        url = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
        content = item.find_element(By.CLASS_NAME, 'carousel-item-content')
        title = content.find_element(By.CLASS_NAME, 'content-title').text
        intro = content.find_element(By.CLASS_NAME, 'content-area').text
        distance = content.find_element(By.CSS_SELECTOR, '.content-address.not-address').text.replace("相距", "")
        price = content.find_element(By.CLASS_NAME, 'content-price').find_element(By.TAG_NAME, 'span').text
        price = int(price.replace(",", ""))
        src = item.find_element(By.CLASS_NAME, 'carousel-list').find_element(By.TAG_NAME, 'img').get_attribute('src')
        near_hid = url.replace("https://rent.591.com.tw/rent-detail-","").replace(".html","")
        data.append(
            {
                'hid':near_hid,
                'url':url,
                'title':title,
                'price':price,
                'distance':distance,
                'intro':intro,
            }
        )

        #* 爬取附近房屋照片, folder 在先前已建立過
        folder_url = f"{photo_path}/{hid}"
        response = requests.get(src)
        if response.status_code == 200:
            image_path = os.path.join(folder_url, f"{near_hid}.jpg")
            with open(image_path, 'wb') as folder:
                folder.write(response.content)

    return data

#todo 主程式開始 --------------------
lock = True
datalist = []
for item in origin_data:
    #* 檢查資料是否已存在 datalist
    if lock and pre_hid == 0:
        lock = False
    elif lock:
        if item['hid'] == pre_hid:
            print(f"Match item {item['hid']}, keep data crawling\n")
            lock = False
            continue
        else:
            continue

    #* from json 抓取資料
    with open(file_path, 'r', encoding='utf-8') as file:
        datalist = json.load(file)

    #* 開啟網頁
    driver.get(item['url'])

    #* 處理請求過快
    check_request_success(driver)

    #* 處理物件不存在
    if data_exist(driver, item):
        continue

    #* 滑到底
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    #todo 開始爬取資料
    #* houseinfo
    houseinfo = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'houseInfo'))
    )
    houseinfo = get_houseinfo(houseinfo)

    #* positionround
    positionround = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'positionRound'))
    )
    positionround = get_position_round(positionround)

    #* servicelist
    servicelist = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'service-list-box'))
    )
    servicelist = get_servicelist(servicelist)

    #* remark
    remark = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, '.remark.block'))
    )
    remark = get_remark(remark, item['hid'])

    #* housedetail
    housedetail = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'houseDetail'))
    )
    housedetail = get_housedetail(housedetail)

    #* 模擬滑鼠滑動和網站互動 (591 採用 lazy loading)
    ActionChains(driver).scroll_by_amount(0,-400).perform()
    time.sleep(2)

    #* near
    near = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, 'house-carousel-container'))
    ).find_element(By.CLASS_NAME, 'carousel-inner')
    try:
        near = get_near(near.find_element(By.CLASS_NAME, 'active'), item['hid'])
    except:
        near = []
        print("No nearly item")

    #todo data assign
    data = {
        #* original data
        'hid':item['hid'],
        'url':item['url'],

        #* updated data
        'houseinfo':houseinfo,
        'positionround':positionround,
        'servicelist':servicelist,
        'remark':remark,
        'housedetail':housedetail,
        'near':near
    }

    datalist.append(data)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(datalist, file, ensure_ascii=False, indent=4)

    print(f"Success store {item['hid']} at {file_path}\n")

print('資料爬取結束')