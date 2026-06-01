# Django 線上選擇題測驗系統

## 系統功能

- 使用者註冊、登入、登出
- Django Admin 題庫管理
- 隨機出題
- 選項隨機排列
- 5 題 / 10 題測驗
- 不同題數倒數計時
- 作答後顯示正確答案
- 錯題重複出現
- 個人作答紀錄
- 作答秒數紀錄
- 作答進度監控
- 題目難易度分級

## 安裝步驟

1. 建立虛擬環境

```bash
python -m venv venv

2. 啟動虛擬環境
Windows：

venv\Scripts\activate

3. 安裝套件
pip install -r requirements.txt

4. 啟動伺服器
python manage.py runserver

5. 開啟網站
http://127.0.0.1:8000/


後台管理
http://127.0.0.1:8000/admin/