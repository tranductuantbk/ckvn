import os

# 1. Tạo các thư mục
folders = ['pages', 'utils', 'data']
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# 2. Tạo các file trống với tên chuẩn xác
files = [
    'app.py',
    'requirements.txt',
    'pages/1_📊_Chi_Bao.py',
    'pages/2_🦈_Dong_Tien_Ca_Map.py',
    'pages/3_🏦_Quy_Dau_Tu.py',
    'pages/4_📰_Tin_Tuc.py',
    'utils/data_fetcher.py',
    'utils/ai_agent.py'
]

for file in files:
    with open(file, 'w', encoding='utf-8') as f:
        pass

print("Đã khởi tạo xong cấu trúc dự án Quant Trading Hub!")