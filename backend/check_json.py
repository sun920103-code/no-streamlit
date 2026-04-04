import json
import os

summary_path = r'd:\No Streamlit\backend\data\client_fund_summary.json'
if os.path.exists(summary_path):
    with open(summary_path, 'r', encoding='utf-8') as f:
        print(json.load(f))
else:
    print("File not found")
