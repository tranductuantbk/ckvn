import streamlit as st
import pandas as pd
import plotly.graph_objects as gr
from plotly.subplots import make_subplots
from vnstock import stock_historical_data
from datetime import datetime, timedelta
import google.generativeai as genai 

# 1. CẤU HÌNH TRANG & GOOGLE AI
st.set_page_config(
    page_title="Quant Trading Hub", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# LƯU Ý: Anh dán API Key của Gemini vào đây để AI hoạt động
GOOGLE_API_KEY = "DIEN_API_KEY_CUA_ANH_VAO_DAY" 
if GOOGLE_API_KEY != "DIEN_API_KEY_CUA_ANH_VAO_DAY":
    genai.configure(api_key=GOOGLE_API_KEY)

# 2. KHỞI TẠO SESSION STATE (BỘ NHỚ HỆ THỐNG)
if 'global_ticker' not in st.session_state:
    st.session_state['global_ticker'] = 'SSI'
if 'ai_context' not in st.session_state:
    st.session_state['ai_context'] = {'chi_bao': '', 'dong_tien': '', 'tin_tuc': ''}
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# 3. SIDEBAR (THANH ĐIỀU HƯỚNG BÊN TRÁI)
with st.sidebar:
    st.title("⚙️ Điều Khiển")
    st.markdown("---")
    
    new_ticker = st.text_input("Nhập mã Cổ phiếu:", value=st.session_state['global_ticker']).upper()
    
    # KÍCH HOẠT KHUNG CHỌN THỜI GIAN
    time_range = st.selectbox("Khoảng thời gian xem:", ["1 Tháng", "3 Tháng", "6 Tháng", "1 Năm"], index=1)
    
    # Chuyển đổi lựa chọn thành số ngày
    days_map = {"1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365}
    st.session_state['time_delta'] = days_map[time_range]
    
    if new_ticker != st.session_state['global_ticker']:
        st.session_state['global_ticker'] = new_ticker
        # Reset dữ liệu cũ khi đổi mã mới
        st.session_state['ai_context'] = {k: '' for k in st.session_state['ai_context']}
        st.session_state['chat_history'] = []
        st.rerun()
    
    st.info("💡 Mẹo: Hãy ghé thăm các trang 'Chỉ báo', 'Dòng tiền' ở menu bên trái để nạp dữ liệu cho AI.")

# 4. HÀM VẼ BIỂU ĐỒ CHUẨN TRADINGVIEW
def plot_chart(symbol, delta_days):
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=delta_days)).strftime('%Y-%m-%d')
    
    try:
        df = stock_historical_data(
            symbol=symbol, start_date=start_date, end_date=end_date, resolution="1D", type="stock"
        )
        
        # Chia 2 khung: Khung trên vẽ Nến (chiếm 75%), khung dưới vẽ Volume (chiếm 25%)
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.75, 0.25]
        )
        
        # 1. Vẽ nến Nhật (Màu chuẩn TradingView)
        fig.add_trace(gr.Candlestick(
            x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], 
            name='Giá',
            increasing_line_color='#26a69a', increasing_fillcolor='#26a69a', # Màu xanh TV
            decreasing_line_color='#ef5350', decreasing_fillcolor='#ef5350'  # Màu đỏ TV
        ), row=1, col=1)
        
        # 2. Vẽ Volume
        # Màu volume đi theo màu nến (giá tăng volume xanh, giá giảm volume đỏ)
        colors = ['#26a69a' if row['close'] >= row['open'] else '#ef5350' for index, row in df.iterrows()]
        fig.add_trace(gr.Bar(
            x=df['time'], y=df['volume'], name='Khối lượng', marker_color=colors, opacity=0.8
        ), row=2, col=1)
        
        # 3. Tinh chỉnh giao diện giống TradingView Dark Mode
        fig.update_layout(
            title=f"<b>{symbol}</b> - Cập nhật dữ liệu {time_range} gần nhất",
            title_font=dict(size=18, color='white'),
            template="plotly_dark",
            paper_bgcolor='#131722', # Nền ngoài TV
            plot_bgcolor='#131722',  # Nền trong TV
            height=600,
            margin=dict(l=10, r=10, b=10, t=40),
            showlegend=False,
            xaxis_rangeslider_visible=False # Tắt cái thanh cuộn ngang xấu xí
        )
        
        # 4. Loại bỏ khoảng trống Thứ 7, CN và làm mờ đường lưới
        fig.update_xaxes(
            rangebreaks=[dict(bounds=["sat", "mon"])], # Cắt bỏ cuối tuần
            showgrid=True, gridwidth=1, gridcolor='#2B2B43', # Lưới TV
            row=1, col=1
        )
        fig.update_xaxes(
            rangebreaks=[dict(bounds=["sat", "mon"])], 
            showgrid=True, gridwidth=1, gridcolor='#2B2B43',
            row=2, col=1
        )
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#2B2B43', row=1, col=1)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#2B2B43', row=2, col=1)
        
        return fig
    except Exception as e:
        st.error(f"Lỗi khi vẽ biểu đồ: {e}")
        return None

# 5. GIAO DIỆN CHÍNH (MAIN DASHBOARD)
st.title(f"🚀 Quant Trading Hub: {st.session_state['global_ticker']}")

col1, col2 = st.columns([6.5, 3.5]) # Chỉnh lại tỷ lệ cho biểu đồ rộng hơn một chút

with col1:
    with st.spinner("Đang kết nối dữ liệu sàn giao dịch..."):
        fig = plot_chart(st.session_state['global_ticker'], st.session_state['time_delta'])
        if fig:
            # Gắn biểu đồ vào giao diện, bỏ đi các viền mặc định
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.subheader("🤖 Trợ lý AI Phân Tích")
    
    # Kiểm tra bộ nhớ dữ liệu hiện tại
    context_data = st.session_state['ai_context']
    data_count = sum(1 for v in context_data.values() if v != '')
    
    # Hiển thị trạng thái nạp dữ liệu
    if data_count == 0:
        st.warning("⚠️ AI chưa có dữ liệu. Anh hãy chọn các trang con bên trái để hệ thống quét dữ liệu trước.")
    elif data_count < 3:
        st.info(f"⚡ Đã nạp {data_count}/3 nguồn dữ liệu. Anh có thể phân tích ngay hoặc nạp thêm để chính xác hơn.")
    else:
        st.success("✅ Dữ liệu đã đầy đủ! AI sẵn sàng đưa ra nhận định chuyên sâu.")

    # NÚT BẤM AI LUÔN MỞ
    if st.button("🌟 Lập báo cáo phân tích chi tiết"):
        if GOOGLE_API_KEY == "DIEN_API_KEY_CUA_ANH_VAO_DAY":
            st.error("❌ Anh chưa điền API Key của Gemini ở đầu file app.py!")
        else:
            # Gom tất cả dữ liệu đang có vào prompt
            full_prompt = f"""
            Bạn là một chuyên gia phân tích chứng khoán Việt Nam cao cấp. 
            Dựa trên dữ liệu thu thập được về mã {st.session_state['global_ticker']}:
            
            [CHỈ BÁO KỸ THUẬT]: {context_data['chi_bao'] if context_data['chi_bao'] else 'Chưa có dữ liệu'}
            [DÒNG TIỀN SMART MONEY]: {context_data['dong_tien'] if context_data['dong_tien'] else 'Chưa có dữ liệu'}
            [TIN TỨC THỊ TRƯỜNG]: {context_data['tin_tuc'] if context_data['tin_tuc'] else 'Chưa có dữ liệu'}
            
            Hãy đưa ra báo cáo theo cấu trúc:
            1. Đánh giá tổng quan xu hướng.
            2. Phân tích sự đồng thuận giữa giá, khối lượng và tin tức.
            3. Khuyến nghị hành động (Mua/Bán/Quan sát) kèm vùng giá mục tiêu nếu có.
            Trả lời bằng tiếng Việt, phong cách Quant Trading chuyên nghiệp.
            """
            
            with st.spinner("AI đang tổng hợp và suy luận dữ liệu..."):
                try:
                    model = genai.GenerativeModel('gemini-pro')
                    response = model.generate_content(full_prompt)
                    st.session_state['chat_history'].append({"role": "assistant", "content": response.text})
                except Exception as e:
                    st.error(f"Lỗi kết nối AI: {e}")

    # Hiển thị nội dung chat
    for message in st.session_state['chat_history']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Tự động dọn dẹp sidebar để tập trung vào nội dung chính
st.markdown("""<style>div[data-testid="stSidebarNav"] { margin-bottom: 2rem; }</style>""", unsafe_allow_html=True)
