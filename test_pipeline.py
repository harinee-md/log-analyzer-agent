import requests
import time
import os

url = 'http://127.0.0.1:8000/api/pipeline/analyze'
file_path = 'log file (1).xlsx'

print(f"Testing API at {url} with {file_path}")

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

files = {'file': ('test.xlsx', open(file_path, 'rb'), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}

# Try up to 5 times
for i in range(5):
    try:
        print(f"Attempt {i+1}...")
        response = requests.post(url, files=files, params={'use_llm': False})
        
        if response.status_code == 200:
            print('Success!')
            data = response.json()
            print(f"Total conversations: {data.get('total_conversations')}")
            
            overall = data.get('overall', {})
            print(f"Composite Score: {overall.get('composite_score')}")
            
            labels = overall.get('label_distribution', {})
            print(f"Labels: {labels}")
            break
        else:
            print(f'Failed: {response.status_code} - {response.text}')
            time.sleep(2)
            
    except Exception as e:
        print(f'Connection failed, retrying... {e}')
        time.sleep(2)
