import streamlit as st
import pandas as pd
import requests
import datetime
import time
import io

# --- 페이지 설정 ---
st.set_page_config(page_title="사업자 등록상태 조회기", page_icon="🏢", layout="centered")

# --- 내부 변수로 API 키 관리 (Raw string 처리로 오류 방지) ---
# 키 앞뒤에 r을 붙여 특수문자 처리 오류를 방지합니다.
INTERNAL_API_KEY = r"hoRuQGqHatZNJVYlmOeRK1H10ejjrHRPkwddmbLJtecpyFjxV4ObhOSZsMROb11eldnnNDJIiP1QY%2B0SvUZlJg%3D%3D"

# --- 커스텀 스타일링 ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="stSidebar"] { background-color: #1A1C24; }
    .stButton>button {
        width: 100%; border-radius: 8px; height: 3.5em;
        background-color: #4F46E5; color: white !important; font-weight: bold; border: none;
    }
    .stButton>button:hover { background-color: #6366F1; color: white !important; }
    /* 텍스트 가독성 확보 */
    .stMarkdown, p, span { color: #E2E8F0 !important; }
    h1, h2, h3 { color: #FFFFFF !important; }
    </style>
    """, unsafe_allow_html=True)

def check_business_status(df, api_key):
    # f-string 대신 직접 결합하여 % 문자 관련 오류 원천 차단
    api_url = "https://api.odcloud.kr/api/nts-businessman/v1/status?serviceKey=" + api_key
    stt_list, tax_list, dt_list = [], [], []
    total_rows = len(df)
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for start_idx in range(0, total_rows, 100):
        end_idx = min(start_idx + 100, total_rows)
        # 하이픈 제거 및 문자열 변환
        business_numbers = df['사업자번호'].iloc[start_idx:end_idx].astype(str).str.replace(r'[^0-9]', '', regex=True).tolist()
        data = {"b_no": business_numbers}
        
        try:
            response = requests.post(api_url, json=data, headers={'Content-Type': 'application/json'}, timeout=10)
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
                    stt_list.append('API오류')
                    tax_list.append('API오류')
                    dt_list.append('-')
        except Exception as e:
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

# --- 메인 UI ---
st.title("🏢 사업자 등록상태 일괄 조회")
st.markdown("---")

with st.sidebar:
    st.header("⚙️ 시스템 설정")
    st.success("✅ API 인증 모드 활성화")
    st.divider()
    st.markdown("### ⚠️ 사용 안내")
    st.info("사업자번호 컬럼이 포함된 파일을 올려주세요.")

uploaded_file = st.file_uploader("검색할 파일을 업로드하세요", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    # 파일 확장자에 따른 읽기
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"📂 파일 로드 완료: {len(df)}건")
    st.dataframe(df.head(5), use_container_width=True)

    if '사업자번호' not in df.columns:
        st.error("❌ '사업자번호' 컬럼을 찾을 수 없습니다. 컬럼명을 확인해주세요.")
    else:
        # 버튼 클릭 시 동작 보장
        if st.button("실시간 상태 조회 시작", key="start_btn"):
            with st.spinner('국세청 데이터를 조회 중입니다...'):
                start_time = time.time()
                result_df = check_business_status(df, INTERNAL_API_KEY)
                duration = round(time.time() - start_time, 2)
                
                st.divider()
                st.subheader("✅ 조회 완료")
                st.write(f"⏱️ 소요 시간: {duration}초")
                st.dataframe(result_df, use_container_width=True)
                
                # 결과 다운로드 로직
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    result_df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 결과 엑셀 파일 다운로드",
                    data=buffer.getvalue(),
                    file_name=f"biz_result_{datetime.datetime.now().strftime('%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
