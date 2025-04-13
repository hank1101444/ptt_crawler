import requests  

apis = [
    {
        'url': 'https://opendata.tycg.gov.tw/api/dataset/a4082497-a866-4fa1-8ebb-4dc9c6e5c46c/resource/22b7362c-04cc-439f-b268-c263bdfc52cb/download',
        'filename': 'api.csv'  
    },
    # {
    #     'url': 'https://第二個API網址',
    #     'filename': 'api2.csv'
    # }
]

for api in apis:
    # 送出 GET 請求取得資料
    response = requests.get(api['url'])

    # 如果成功下載（狀態碼為 200）
    if response.status_code == 200:
        # 將內容寫入對應的檔案名稱（以二進位方式寫入）
        with open(api['filename'], 'wb') as f:
            f.write(response.content)
        print(f"✅ 檔案已成功儲存為 {api['filename']}") 
    else:
        print(f"❌ 下載失敗（{api['filename']}），狀態碼：{response.status_code}")
