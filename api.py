import requests

# API URL 與 對應輸出檔名
apis = [
    {
        'url': 'https://opendata.tycg.gov.tw/api/dataset/a4082497-a866-4fa1-8ebb-4dc9c6e5c46c/resource/22b7362c-04cc-439f-b268-c263bdfc52cb/download',
        'filename': 'api.csv'
    },
    # {
    #     'url': 'https://',
    #     'filename': 'api2.csv'
    # }
]

for api in apis:
    response = requests.get(api['url'])

    if response.status_code == 200:
        with open(api['filename'], 'wb') as f:
            f.write(response.content)
        print(f"✅ 檔案已成功儲存為 {api['filename']}")
    else:
        print(f"❌ 下載失敗（{api['filename']}），狀態碼：{response.status_code}")
