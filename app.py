import streamlit as st
import pandas as pd
import plotly.graph_objects as gr
from vnstock import stock_historical_data
from datetime import datetime, timedelta
import google.generativeai as genai 

# 1. CẤU HÌNH TRANG & GOOGLE AI
st.set_page_config(page_title="Quant Trading Hub", page_icon="📈", layout="wide")

# Đừng quên điền API Key vào đây nhé anh
GOOGLE_API_KEY = "DIEN_API_KEY_CUA_ANH_VAO_DAY" 
if GOOGLE_API_KEY != "DIEN_API_KEY_CUA_ANH_VAO_DAY":
    genai.configure(api_key=GOOGLE_API_KEY)

# 2. KHỞI TẠO SESSION STATE
if 'global_ticker' not in st.session_state:
    st.session_state['global_ticker'] = 'SSI'
if 'ai_context' not in st.session_state:
    st.session_state['ai_context'] = {'chi_bao': '', 'dong_tien': '', 'tin_tuc': ''}
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# 3. SIDEBAR
with st.sidebar:
    st.title("⚙️ Điều Khiển")
    new_ticker = st.text_input("Mã Cổ phiếu:", value=st.session_state['global_ticker']).upper()
    if new_ticker != st.session_state['global_ticker']:
        st.session_state['global_ticker'] = new_ticker
        st.session_state['ai_context'] = {k: '' for k in st.session_state['ai_context']}
        st.rerun()
    
    st.info("💡 Mẹo: Hãy ghé thăm các trang 'Chỉ báo', 'Dòng tiền' và 'Tin tức' ở menu bên trái để AI có đủ dữ liệu phân tích mã này.")

# 4. HÀM VẼ BIỂU ĐỒ NẾN (Đã sửa lỗi vnstock)
def plot_chart(symbol):
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
    df = stock_historical_data(symbol=symbol, start_date=start_date, end_date=end_date, resolution="1D", type="stock")
    
    fig = gr.Figure(data=[gr.Candlestick(
        x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Nến Nhật'
    )])
    fig.update_layout(title=f"Diễn biến giá {symbol}", yaxis_title="Giá (VND)", template="plotly_dark", height=500)
    return fig

# 5. GIAO DIỆN CHÍNH
st.title(f"🚀 Quant Trading Hub: {st.session_state['global_ticker']}")

col1, col2 = st.columns([6, 4])

with col1:
    st.subheader("📈 Biểu đồ kỹ thuật")
    with st.spinner("Đang tải biểu đồ..."):
        fig = plot_chart(st.session_state['global_ticker'])
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("🤖 Trợ lý AI Phân Tích")
    
    context_data = st.session_state['ai_context']
    is_ready = all(v != '' for v in context_data.values())
    
    if not is_ready:
        st.warning("AI đang thiếu dữ liệu. Anh hãy nhấn vào các trang con bên trái để hệ thống quét dữ liệu trước nhé!")
    
    if st.button("🌟 Lập báo cáo phân tích chi tiết", disabled=not is_ready):
        full_prompt = f"""
        Bạn là một chuyên gia phân tích chứng khoán Việt Nam cao cấp. 
        Dựa trên dữ liệu sau đây về mã {st.session_state['global_ticker']}:
        
        {context_data['chi_bao']}
        {context_data['dong_tien']}
        {context_data['tin_tuc']}
        
        Hãy đưa ra nhận định:
        1. Xu hướng ngắn hạn là gì?
        2. Điểm tích cực và tiêu cực hiện tại.
        3. Lời khuyên Hành động (Mua/Bán/Theo dõi) và tại sao?
        Hãy trả lời bằng tiếng Việt, phong cách chuyên nghiệp, quyết đoán.
        """
        
        if GOOGLE_API_KEY == "DIEN_API_KEY_CUA_ANH_VAO_DAY":
            st.error("Anh chưa điền API Key của Gemini vào code!")
        else:
            with st.spinner("AI đang 'đọc' dữ liệu và suy luận..."):
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(full_prompt)
                st.session_state['chat_history'].append({"role": "assistant", "content": response.text})

    for message in st.session_state['chat_history']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
