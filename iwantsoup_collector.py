import os
import sys
import urllib.request
import json
import pandas as pd
import time

client_id = "Yem87F_eBlSSnBoVtAy1"
client_secret = "Oli1B6JPgx"

def fetch_100_at_bundang(keyword):
    full_query = f"분당 {keyword}"
    all_items = []

    for i in range(20):
        start_index = (i * 5) + 1
        encText = urllib.parse.quote(full_query)
        url = f"https://openapi.naver.com/v1/search/local.json?query={encText}&display=5&start={start_index}"
        
        request = urllib.request.Request(url)
        request.add_header("X-Naver-Client-Id", client_id)
        request.add_header("X-Naver-Client-Secret", client_secret)
        
        try:
            response = urllib.request.urlopen(request)
            if response.getcode() == 200:
                data = json.loads(response.read().decode('utf-8'))
                items = data.get('items', [])
                
                if not items:
                    break
                    
                for item in items:
                    all_items.append({
                        'restaurant_name': item['title'].replace('<b>', '').replace('</b>', ''),
                        'category': item['category'],
                        'address': item['address'],
                        'road_address': item['roadAddress'],
                        'search_keyword': keyword 
                    })
            time.sleep(0.05)
        except Exception as e:
            print(f"Error fetching {full_query}: {e}")
            break
            
    return pd.DataFrame(all_items)

print("분당 지역 데이터 전수 수집을 시작합니다.")

print("그룹 A: '국물' 수집 중...")
df_soup = fetch_100_at_bundang("국물")

print("그룹 B: 구체 메뉴들 수집 중...")
keywords_b = ["국밥", "부대찌개", "쌀국수", "짬뽕", "마라탕", "김치찌개", "육개장", "곰탕", "칼국수", "라멘"]
df_list_b = []
for kw in keywords_b:
    print(f" - '{kw}' 수집 중...")
    df_list_b.append(fetch_100_at_bundang(kw))

df_specific = pd.concat(df_list_b, ignore_index=True)

final_df = pd.concat([df_soup, df_specific], ignore_index=True)
final_df.to_csv("iwantsoup_bundang_all.csv", index=False, encoding='utf-8-sig')

print("-" * 30)
print(f"수집 완료! 총 {len(final_df)}개의 식당 데이터가 저장되었습니다.")
print("파일명: iwantsoup_bundang_all.csv")