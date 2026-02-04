-- 1. 중복 제거
CREATE OR REPLACE TABLE `bundang_soup.cleaned_restaurants` AS
SELECT 
    ROW_NUMBER() OVER() AS restaurant_id,
    *
FROM (
    SELECT DISTINCT 
        restaurant_name, 
        category, 
        address, 
        road_address 
    FROM `bundang_soup.raw_search_data`
);

-- 2. Categories 테이블 생성
CREATE OR REPLACE TABLE `bundang_soup.Categories` AS
SELECT 
    ROW_NUMBER() OVER() AS category_id,
    category AS category_name
FROM (SELECT DISTINCT category FROM `bundang_soup.raw_search_data`);

-- 3. Keywords 테이블 생성
CREATE OR REPLACE TABLE `bundang_soup.Keywords` AS
SELECT 
    ROW_NUMBER() OVER() AS keyword_id,
    search_keyword AS keyword_name,
    CASE WHEN search_keyword = '국물' THEN TRUE ELSE FALSE END AS is_broad
FROM (SELECT DISTINCT search_keyword FROM `bundang_soup.raw_search_data`);

-- 4. Search_Logs 테이블 생성
CREATE OR REPLACE TABLE `bundang_soup.Search_Logs` AS
SELECT 
    ROW_NUMBER() OVER() AS log_id,
    r.restaurant_id,
    k.keyword_id,
    raw.search_keyword 
FROM `bundang_soup.raw_search_data` AS raw
JOIN `bundang_soup.cleaned_restaurants` AS r ON raw.restaurant_name = r.restaurant_name AND raw.address = r.address
JOIN `bundang_soup.Keywords` AS k ON raw.search_keyword = k.keyword_name;

--5. 국물 키워드 검색 노출율 및 누락율 계산
WITH total_counts AS (
  SELECT COUNT(*) AS total_restaurants FROM `bundang_soup.cleaned_restaurants`
),
exposed_counts AS (
  SELECT COUNT(DISTINCT r.restaurant_id) AS exposed_restaurants
  FROM `bundang_soup.cleaned_restaurants` r
  JOIN `bundang_soup.Search_Logs` l ON r.restaurant_id = l.restaurant_id
  JOIN `bundang_soup.Keywords` k ON l.keyword_id = k.keyword_id
  WHERE k.keyword_name = '국물'
)
SELECT 
  total_restaurants AS total_restaurant_count,
  exposed_restaurants AS exposed_in_search_count,
  ROUND((exposed_restaurants / total_restaurants) * 100, 1) AS exposure_rate_pct,
  100 - ROUND((exposed_restaurants / total_restaurants) * 100, 1) AS omission_rate_pct
FROM total_counts, exposed_counts;

--6. 진짜 국물 요리인데 검색에선 안 나오는 식당 TOP 10
SELECT 
  r.restaurant_name, 
  r.category, 
  r.address,
FROM `bundang_soup.cleaned_restaurants` r
LEFT JOIN (
  SELECT DISTINCT restaurant_id 
  FROM `bundang_soup.Search_Logs` l
  JOIN `bundang_soup.Keywords` k ON l.keyword_id = k.keyword_id
  WHERE k.keyword_name = '국물'
) AS exposed ON r.restaurant_id = exposed.restaurant_id
WHERE exposed.restaurant_id IS NULL -- 검색 결과에 없는 식당만 추출
LIMIT 10;

-- 7. 식당 정보에 노출/누락 라벨 붙이기
CREATE OR REPLACE TABLE `bundang_soup.map_visualization_data` AS
SELECT 
    r.*,
    CASE 
        WHEN exposed.restaurant_id IS NOT NULL THEN 'Exposed'
        ELSE 'Omitted'
    END AS exposure_status
FROM `bundang_soup.cleaned_restaurants` r
LEFT JOIN (
    SELECT DISTINCT restaurant_id 
    FROM `bundang_soup.Search_Logs` l
    JOIN `bundang_soup.Keywords` k ON l.keyword_id = k.keyword_id
    WHERE k.keyword_name = '국물'
) AS exposed ON r.restaurant_id = exposed.restaurant_id;



-- 수정/ 중복 제거
WITH exposed_restaurants AS (
  SELECT DISTINCT r.restaurant_name
  FROM `bundang_soup.cleaned_restaurants` r
  JOIN `bundang_soup.Search_Logs` l ON r.restaurant_id = l.restaurant_id
  JOIN `bundang_soup.Keywords` k ON l.keyword_id = k.keyword_id
  WHERE k.keyword_name = '국물'
)
SELECT 
  COUNT(m.restaurant_name) AS total_survey, 
  COUNT(e.restaurant_name) AS exposed, 
  ROUND((1 - COUNT(e.restaurant_name) / COUNT(m.restaurant_name)) * 100, 1) AS final_omission_rate
FROM `bundang_soup.manual_restaurants_raw` m
LEFT JOIN exposed_restaurants e ON m.restaurant_name = e.restaurant_name;

-- 전체 식당 중 시맨틱 갭이 발생하는 비중
SELECT 
  semantic_gap, 
  COUNT(*) AS count,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER() * 100, 1) AS percentage
FROM `bundang_soup.manual_logic_categorization`
GROUP BY semantic_gap;

-- match_trigger별 분포 확인
SELECT 
  match_trigger, 
  COUNT(*) AS count,
  ROUND(COUNT(*) / SUM(COUNT(*)) OVER() * 100, 1) AS percentage
FROM `bundang_soup.manual_logic_categorization`
GROUP BY match_trigger
ORDER BY count DESC;

-- 검색 의도와 맞지 않는 '노이즈' 식당 리스트 추출
SELECT 
  restaurant_name, 
  insight_memo 
FROM `bundang_soup.manual_logic_categorization`
WHERE property_match IS FALSE; 

