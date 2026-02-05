import streamlit as st
import pandas as pd
import requests
import datetime
import time
import io

# --- 페이지 설정 (Dark 모드 지향) ---
st.set_page_config(page_title="사업자 상태 조회기", page_icon="🏢", layout="centered")

# --- 커스텀 스타일링 (어두운 배경 및 폰트 설정) ---
st.markdown("""
    <style>
    /* 메인 배경 및 글자색 */
    .stApp {
        background-color: #0E1117;
        color: #FFFFFF;
    }
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #1A1C24;
    }
    /* 버튼 스타일 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3.5em;
        background-color: #4F46E5;
        color: white;
        border: none;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #6366F1;
        border: none;
        color: white;
    }
    /* 카드 느낌의 정보 박스 */
    div.stAlert {
        background-color: #1E293B;
        color: #E2E8F0;
        border: 1px solid #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 함수 정의 ---
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
        status_text.text(f"🚀 처리 중... {percent}% ({end_idx}/{total_rows})")

    df['사업자 상태'] = stt_list
    df['세금 유형'] = tax_list
    df['세금 유형 변경일'] = dt_list
    return df

# --- 메인 화면 UI ---
st.title("🏢 사업자 등록상태 일괄 조회")
st.markdown("---")

# 사이드바에서 API KEY 숨김 처리 (비밀번호 형식)
with st.sidebar:
    st.header("🔐 보안 설정")
    # type="password"를 사용하여 화면에 문자가 노출되지 않게 함
    user_api_key = st.text_input("공공데이터 API KEY 입력", 
                                value="hoRuQGqHatZNJVYlmOeRK1H10ejjrHRPkwddmbLJtecpyFjxV4ObhOSZsMROb11eldnnNDJIiP1QY%2B0SvUZlJg%3D%3D",
                                type="password",
                                help="공공데이터 포털에서 발급받은 서비스키를 입력하세요.")
    
    st.markdown("### ⚠️ 사용 안내")
    st.info("""
    - 컬럼명: **'사업자번호'** 필수
    - 파일형식: Excel, CSV 지원
    - 하이픈(-)은 자동 제거됩니다.
    """)

# 파일 업로드 부분
uploaded_file = st.file_uploader("검색할 파일을 업로드하세요", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"📂 파일 읽기 성공: {len(df)}건")
    
    # 데이터 미리보기 (어두운 테마용 데이터프레임 스타일)
    st.dataframe(df.head(3), use_container_width=True)

    if '사업자번호' not in df.columns:
        st.error("❌ '사업자번호' 컬럼을 찾을 수 없습니다.")
    else:
        if st.button("실시간 상태 조회 시작"):
            if not user_api_key:
                st.warning("API 키를 입력해주세요.")
            else:
                start_time = time.time()
                result_df = check_business_status(df, user_api_key)
                duration = round(time.time() - start_time, 2)
                
                st.divider()
                st.subheader("✅ 조회 완료")
                st.write(f"⏱️ 소요 시간: {duration}초")
                st.dataframe(result_df, use_container_width=True)
                
                # 결과 다운로드
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    result_df.to_excel(writer, index=False)
                
                st.download_button(
                    label="📥 결과 엑셀 파일 다운로드",
                    data=buffer.getvalue(),
                    file_name=f"biz_result_{datetime.datetime.now().strftime('%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
