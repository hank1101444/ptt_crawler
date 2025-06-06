import requests  

apis = [
    {
        'url': 'https://opendata.tycg.gov.tw/api/dataset/a4082497-a866-4fa1-8ebb-4dc9c6e5c46c/resource/22b7362c-04cc-439f-b268-c263bdfc52cb/download',
        'filename': 'api1.csv'  
    },
    {
        'url': 'https://opendata.tycg.gov.tw/api/dataset/dab92074-e386-4fe0-a2cd-e4f2cd0955f0/resource/410844b8-066d-48bf-b917-5ede11f0c276/download',
        'filename': 'api2.csv'
    }
]

for api in apis:
    response = requests.get(api['url'])

    if response.status_code == 200:
        # ✅ 嘗試用 apparent_encoding 偵測
        response.encoding = response.apparent_encoding

        # ✅ 將內容寫為 UTF-8 編碼
        with open(api['filename'], 'w', encoding='utf-8', newline='') as f:
            f.write(response.text)

        print(f"✅ 檔案已成功儲存為 {api['filename']}，原始編碼為 {response.encoding}")
    else:
        print(f"❌ 下載失敗：{api['filename']}，狀態碼：{response.status_code}")

