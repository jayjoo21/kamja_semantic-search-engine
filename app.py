import streamlit as st
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer, util
import folium

from streamlit_folium import st_folium 

st.set_page_config(page_title="kamja", page_icon="🥔", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Nanum+Gothic:wght@700;800;900&display=swap');
    
    .main { background-color: #ffffff; }
    [data-testid="stSidebar"] { display: none; }
    :root { --naver-green: #03C75A; }
    
    /* 1. k a m j a 로고: 네이버 스타일의 압도적 두께감 */
    .brand-logo {
        color: var(--naver-green);
        font-family: 'Nanum Gothic', sans-serif;
        font-weight: 950 !important; 
        font-size: 75px !important;
        text-transform: lowercase;
        letter-spacing: 12px !important;
        line-height: 1;
        -webkit-text-stroke: 2.5px var(--naver-green); /* 외곽선으로 두께 증폭 */
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* 2. 검색창: 세로 폭 조절 (padding 값을 조절하여 두께를 맞추세요) */
    div[data-baseweb="input"] {
        border: 2px solid #e3e5e8 !important;
        border-radius: 45px !important;
        padding: 18px 35px !important; /* 이 값을 15~25 사이로 조절해보세요 */
        min-height: 60px !important;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08) !important;
    }
    .stTextInput input {
        font-size: 15px !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="input"]:focus-within { border-color: var(--naver-green) !important; }

    /* 결과 카드 및 버튼 스타일 */
    .res-card {
        border: 1px solid #f0f0f0; border-radius: 12px; padding: 22px;
        margin-bottom: 20px; background: #ffffff; transition: transform 0.2s ease;
    }
    .res-card:hover { transform: translateY(-3px); border-color: var(--naver-green); }
    .res-name { font-size: 22px; font-weight: bold; color: #111; margin-bottom: 8px; }
    .logic-explanation {
        background: #f8fcf9; border-left: 4px solid var(--naver-green);
        padding: 12px; margin: 12px 0; font-size: 14px; line-height: 1.6; color: #333;
    }
    .map-link-btn {
        display: inline-block; margin-top: 12px; padding: 10px 20px;
        background-color: #ffffff; color: var(--naver-green);
        border: 1.5px solid var(--naver-green); border-radius: 6px;
        font-size: 13px; font-weight: bold; text-decoration: none;
    }
    .map-link-btn:hover { background-color: var(--naver-green); color: #ffffff; }
    .meta-info { font-size: 13px; color: #777; display: flex; gap: 15px; }
    .footer { text-align: center; padding: 40px; color: #bbb; font-size: 12px; border-top: 1px solid #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로드 엔진
@st.cache_resource
def load_kamja_engine():
    df = pd.read_csv('kamja_final_data.csv')
    embeddings = np.load('kamja_embeddings.npy')
    model = SentenceTransformer('jhgan/ko-sroberta-multitask')
    return df, embeddings, model

df, enriched_embeddings, model = load_kamja_engine()

# 상단 헤더
header_col1, header_col2 = st.columns([1.8, 4], vertical_alignment="center")

with header_col1:
    st.markdown('<div class="brand-logo">kamja</div>', unsafe_allow_html=True)

with header_col2:
    st.markdown("<p style='font-size: 15px; font-weight: bold; margin-bottom: 5px; color: #333;'>맥락으로 검색해보세요!</p>", unsafe_allow_html=True)
    query = st.text_input("검색", placeholder="예: 해장하기 좋은 뜨끈한 국밥", 
                         key="search_bar", label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)

# 메인
col_map, col_results = st.columns([2.8, 2], gap="small")

results = pd.DataFrame()
if query:
    query_vec = model.encode([query])
    sim_scores = util.cos_sim(query_vec, enriched_embeddings)[0].cpu().tolist()
    df['sim_score'] = sim_scores
    df['total_score'] = (df['sim_score'] * 0.4) + (df['n_rating'] * 0.2) + (df['n_reviews'] * 0.2) + (0.5 * 0.2)
    results = df.sort_values(by='total_score', ascending=False).head(10)

# 왼: 지도
with col_map:
    my_lat, my_lon = 37.3595, 127.1054
    m = folium.Map(location=[my_lat, my_lon], zoom_start=15, tiles="cartodbpositron")
    
    if not results.empty:
        for i, row in results.iterrows():
            popup_html = f'<div style="text-align:center;"><b>{row["restaurant_name"]}</b><br>★{row["rating"]:.1f}</div>'
            folium.Marker(
                [row['lat'], row['lon']],
                popup=folium.Popup(popup_html, max_width=200),
                icon=folium.Icon(color='green', icon='cutlery', prefix='fa')
            ).add_to(m)

    map_data = st_folium(m, width=950, height=800, key="kamja_map")

# 우: 검색 결과
with col_results:
    clicked_restaurant = None
    if map_data and map_data.get("last_object_clicked_popup"):
        try:
            clicked_restaurant = map_data["last_object_clicked_popup"].split('<b>')[1].split('</b>')[0].strip()
        except:
            clicked_restaurant = None

    if query and not results.empty:
        if clicked_restaurant:
            match = results[results['restaurant_name'].str.strip() == clicked_restaurant]
            if not match.empty:
                target = match.iloc[0]
                st.markdown(f"### 📍 지도 선택: {clicked_restaurant}")
                st.markdown(f"""
                <div class="res-card" style="border: 3px solid #03C75A; background-color: #f0fff5;">
                    <div class="res-name">{target['restaurant_name']} <span>★{target['rating']:.1f}</span></div>
                    <a href="https://map.naver.com/v5/search/{target['restaurant_name']}" target="_blank" class="map-link-btn">📍 네이버 지도에서 보기</a>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("---")

        st.markdown(f"### 🔍 **'{query}'** 분석 결과")
        with st.container(height=780, border=False):
            for i, row in results.iterrows():
                cat_label = str(row['enriched_category']).split('>')[-1] if pd.notna(row['enriched_category']) else "음식점"
                naver_url = f"https://map.naver.com/v5/search/{row['restaurant_name']}"
                border_style = "border: 2px solid #03C75A;" if row['restaurant_name'].strip() == clicked_restaurant else ""
                
                st.markdown(f"""
                <div class="res-card" style="{border_style}">
                    <div class="res-name">{row['restaurant_name']} <span>★{row['rating']:.1f}</span></div>
                    <div style="margin-bottom: 12px;"><span style="color:#03C75A; font-size:12px; font-weight:bold; border:1px solid #03C75A; padding:2px 8px; border-radius:4px;">{cat_label}</span></div>
                    <div class="logic-explanation"><b>AI 분석:</b> 검색 의도와 <b>{int(row['sim_score']*100)}%</b> 일치합니다.</div>
                    <div class="meta-info"><span>리뷰 {int(row['review_count'])}개</span><span>📍 Naver 본사 인근</span></div>
                    <a href="{naver_url}" target="_blank" class="map-link-btn">📍 네이버 지도 길찾기</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center; padding-top:150px; color:#eee;"><h1 style="font-size:120px;">🥔</h1><p style="color:#ccc; font-size:18px;">맥락 검색을 시작해보세요.</p></div>', unsafe_allow_html=True)

st.markdown('<div class="footer">© 2026 kamja Project. Powered by Naver Map Data & Semantic AI.</div>', unsafe_allow_html=True)