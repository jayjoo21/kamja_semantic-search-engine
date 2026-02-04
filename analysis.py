import pandas as pd

file_path = "iwantsoup_bundang_all.csv"
try:
    df = pd.read_csv(file_path)
except FileNotFoundError:
    print(f"'{file_path}' 파일을 찾을 수 없습니다. 수집 코드를 먼저 실행해 주세요.")
    exit()


# 국물' 키워드로 검색된 장소
group_a_df = df[df['search_keyword'] == '국물']
group_a_names = set(group_a_df['restaurant_name'].unique())

# 구체적인 10개 메뉴로 검색된 장소
group_b_df = df[df['search_keyword'] != '국물']
group_b_names = set(group_b_df['restaurant_name'].unique())

# Semantic Gap 분석 (B에는 있지만 A에는 없는 식당)
semantic_gap_names = list(group_b_names - group_a_names)
missing_rate = (len(semantic_gap_names) / len(group_b_names)) * 100 if group_b_names else 0

# 카테고리별 누락 현황 
df_missing = group_b_df[group_b_df['restaurant_name'].isin(semantic_gap_names)].drop_duplicates('restaurant_name')
category_stats = df_missing['category'].value_counts().head(5)

print("="*50)
print(f"[iwantsoup] 분당 지역 10개 키워드 분석 결과")
print("="*50)
print(f"1. 분석된 총 고유 식당 수: {len(df['restaurant_name'].unique())}개")
print(f"2. 구체 메뉴 검색(그룹 B) 식당 수: {len(group_b_names)}개")
print(f"3. '국물' 검색(그룹 A) 노출 식당 수: {len(group_a_names)}개")
print(f"4. Semantic Gap (누락된 식당): {len(semantic_gap_names)}개")
print(f"5. 누락율(Missing Rate): {missing_rate:.1f}%")
print("-" * 50)
print("업종별 누락 빈도 TOP 5 (시맨틱 갭 원인 후보):")
print(category_stats)
print("-" * 50)
print("누락된 주요 식당 (일부):")
for i, res in enumerate(semantic_gap_names[:15]):
    print(f"{i+1}. {res}")

df.to_csv("bundang_final_for_bigquery.csv", index=False, encoding='utf-8-sig')
print("\n분석 완료! 'bundang_final_for_bigquery.csv'가 생성되었습니다.")

