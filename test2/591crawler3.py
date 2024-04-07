import os
import json

with open('data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

datalist = []
for item in data:
    valid = True
    folder_url = f"D:/gold_house/{item['hid']}"
    if os.path.exists(folder_url):
        for i in datalist:
            if item['hid'] == i['hid']:
                valid = False
                break
        if valid:
            datalist.append(item)

try:
    with open("D:/gold_house/data.json", "w", encoding="utf-8")as file:
        json.dump(datalist, file, ensure_ascii=False, indent=4)
    print('json success')
except Exception as e:
    print('json fails')

print(f"Success create {len(datalist)} data")
        