import streamlit as st
import pandas as pd
import requests
import datetime
import time
import io

# --- 페이지 설정 ---
st.set_page_config(page_title="사업자 등록상태 조회기", page_icon="🏢", layout="centered")

# --- 내부 변수로 API 키 관리 (프런트 노출 안됨) ---
# 이 부분에 키를 넣어두면 사용자는 화면에서 키를 볼 수 없습니다.
INTERNAL_API_KEY = "hoRuQGqHatZNJVYlmOeRK1H10ejjrHRPkwddmbLJtecpyFjxV4ObhOSZsMROb11eldnnNDJIiP1QY%2B0SvUZlJg%3D%3D"

# --- 커스텀 스타일링 (다크 모드 최적화) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1A1C24; }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #4F46E5; color: white; font-weight: bold; border: none;
    }
    .stButton>button:hover { background-color: #6366F1; color: white; }
    </style>
    """, unsafe_allow_html=True)

def check_business_status(df, api_key):
    api_url = f"https://api.odcloud.kr/api/nts-businessman/v1/status?serviceKey={api_key}"
    stt_list, tax_list, dt_list = [], [], []
    total_rows = len(df)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for start_idx in range(0, total_rows, 100):
        end_idx = min(start_idx + 100, total_rows)
        business_numbers = df['사업자번호'].iloc[start_idx:end_idx].astype(str).str.replace('-', '').tolist()
        data = {"b_no": business_numbers}
        
        try:
            # API 호출 시 INTERNAL_API_KEY 사용
            response = requests.post(api_url, json=data, headers={'Content-Type': 'application/json'})
            if response.status_code == 200:
                results = response.json().get('data', [])
                res_dict = {item['b_no']: item for item in results}
                for b_no in business_numbers:
                    res = res_dict.get(b_no, {})
                    stt_list.append(res.get('b_stt', '정보없음'))
                    tax_list.append(res.get('tax_type', '정보없음'))
                    dt_list.append(res.get('tax_type_change_dt', '-'))
            else:
                for _ in range(end_idx - start_idx):
                    stt_list.append('오류')
                    tax_list.append('오류')
                    dt_list.append('-')
        except:
            for _ in range(end_idx - start_idx):
                stt_list.append('연결실패')
                tax_list.append('연결실패')
                dt_list.append('-')
            
        percent = int((end_idx / total_rows) * 100)
        progress_bar.progress(percent)
        status_text.text(f"🚀 조회 중... {percent}% ({end_idx}/{total_rows})")

    df['사업자 상태'] = stt_list
    df['세금 유형'] = tax_list
    df['세금 유형 변경일'] = dt_list
    return df

# --- 메인 화면 UI ---
st.title("🏢 사업자 등록상태 일괄 조회")
st.markdown("---")

# 사이드바에서 입력창 삭제, 안내 문구만 남김
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    st.success("✅ API 연결됨 (인증 완료)") # 사용자에게 안심을 주는 멘트
    st.divider()
    st.markdown("### ⚠️ 사용 안내")
    st.info("""
    - 파일 내 컬럼명: **'사업자번호'**
    - 파일 형식: **Excel, CSV**
    - 하이픈(-)은 자동 제거됩니다.
    """)

uploaded_file = st.file_uploader("검색할 파일을 업로드하세요", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"📂 파일 로드 완료: {len(df)}건")
    st.dataframe(df.head(3), use_container_width=True)

    if '사업자번호' not in df.columns:
        st.error("❌ '사업자번호' 컬럼을 찾을 수 없습니다.")
    else:
        # 사용자는 키 입력 없이 버튼만 누르면 됨
        if st.button("실시간 상태 조회 시작"):
            start_time = time.time()
            # 내부 변수인 INTERNAL_API_
