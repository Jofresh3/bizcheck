import streamlit as st
import pandas as pd
import requests
import datetime
import time

# --- 설정 (Page Config) ---
st.set_page_config(page_title="사업자 등록상태 조회기", page_icon="🏢", layout="centered")

# --- 스타일링 ---
st.markdown("""
    <style>
    .main {
        background-color: #f5f7f9;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 함수 정의 ---
def check_business_status(df, api_key):
    api_url = f"https://api.odcloud.kr/api/nts-businessman/v1/status?serviceKey={api_key}"
    
    # 결과 저장용 리스트
    stt_list, tax_list, dt_list = [], [], []
    
    total_rows = len(df)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 100개씩 나누어 처리
    for start_idx in range(0, total_rows, 100):
        end_idx = min(start_idx + 100, total_rows)
        # 사업자번호를 문자열 리스트로 변환 (하이픈 제거 및 형식 맞춤)
        business_numbers = df['사업자번호'].iloc[start_idx:end_idx].astype(str).str.replace('-', '').tolist()
        
        data = {"b_no": business_numbers}
        
        try:
            response = requests.post(api_url, json=data, headers={'Content-Type': 'application/json'}, verify=True)
            if response.status_code == 200:
                results = response.json().get('data', [])
                # 결과 매핑용 딕셔너리 생성
                res_dict = {item['b_no']: item for item in results}
                
                for b_no in business_numbers:
                    res = res_dict.get(b_no, {})
                    stt_list.append(res.get('b_stt', '정보없음'))
                    tax_list.append(res.get('tax_type', '정보없음'))
                    dt_list.append(res.get('tax_type_change_dt', '-'))
            else:
                for _ in range(end_idx - start_idx):
                    stt_list.append('API 오류')
                    tax_list.append('API 오류')
                    dt_list.append('-')
        except Exception as e:
            st.error(f"오류 발생: {e}")
            break
            
        # 진행률 업데이트
        percent = int((end_idx / total_rows) * 100)
        progress_bar.progress(percent)
        status_text.text(f"처리 중... ({end_idx}/{total_rows})")

    # 데이터프레임 업데이트
    df['사업자 상태'] = stt_list
    df['세금 유형'] = tax_list
    df['세금 유형 변경일'] = dt_list
    
    return df

# --- 메인 화면 UI ---
st.title("🏢 사업자 등록상태 일괄 조회")
st.info("엑셀 또는 CSV 파일을 업로드하여 국세청 등록 상태를 확인하세요.")

# 사이드바 설정
with st.sidebar:
    st.header("⚙️ 설정")
    api_key = st.text_input("공공데이터 API KEY", 
                           value="hoRuQGqHatZNJVYlmOeRK1H10ejjrHRPkwddmbLJtecpyFjxV4ObhOSZsMROb11eldnnNDJIiP1QY%2B0SvUZlJg%3D%3D",
                           type="password")
    st.caption("기본 API 키가 입력되어 있습니다.")
    st.divider()
    st.markdown("⚠️ **주의사항**")
    st.write("1. 파일 내 컬럼명은 반드시 **'사업자번호'**여야 합니다.")
    st.write("2. 하이픈(-)은 자동으로 처리됩니다.")

# 파일 업로드
uploaded_file = st.file_uploader("파일을 선택하세요 (xlsx, csv)", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    # 데이터 로드
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.success(f"✅ 파일 로드 완료! 총 {len(df)}건의 데이터를 확인했습니다.")
    st.dataframe(df.head(5), use_container_width=True) # 미리보기

    if '사업자번호' not in df.columns:
        st.error("❌ 파일에 '사업자번호' 컬럼이 존재하지 않습니다. 컬럼명을 확인해주세요.")
    else:
        if st.button("조회 시작하기"):
            start_time = time.time()
            
            # 조회 실행
            result_df = check_business_status(df, api_key)
            
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            
            st.divider()
            st.balloons() # 완료 효과
            st.subheader("✅ 조회 결과")
            st.write(f"⏱️ 소요 시간: {duration}초")
            
            # 결과 표 출력
            st.dataframe(result_df, use_container_width=True)
            
            # 다운로드 버튼
            output_name = f"result_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # 엑셀 변환 (메모리 내)
            import io
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                result_df.to_excel(writer, index=False)
            
            st.download_button(
                label="📊 결과 엑셀 파일 다운로드",
                data=buffer.getvalue(),
                file_name=output_name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
