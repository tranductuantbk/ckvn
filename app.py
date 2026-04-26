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

# 2. KHỞI TẠO SESSION STATE
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
    
    st.markdown("### ⏱️ Cấu hình Biểu đồ")
    
    # KÍCH HOẠT CHỌN KHUNG NẾN (Giờ, Ngày, Tuần)
    candle_resolution = st.selectbox(
        "1. Chọn Khung Nến:", 
        ["1 Giờ (1H)", "1 Ngày (1D)", "1 Tuần (1W)"], 
        index=1
    )
    res_map = {"1 Giờ (1H)": "1H", "1 Ngày (1D)": "1D", "1 Tuần (1W)": "1W"}
    st.session_state['resolution'] = res_map[candle_resolution]

    # KÍCH HOẠT CHỌN KHOẢNG THỜI GIAN LÙI LẠI
    time_range = st.selectbox(
        "2. Dữ liệu lùi lại:", 
        ["1 Tuần", "1 Tháng", "3 Tháng", "6 Tháng", "1 Năm"], 
        index=2
    )
    days_map = {"1 Tuần": 7, "1 Tháng": 30, "3 Tháng": 90, "6 Tháng": 180, "1 Năm": 365}
    st.session_state['time_delta'] = days_map[time_range]
    
    if new_ticker != st.session_state['global_ticker']:
        st.session_state['global_ticker'] = new_ticker
        # Reset dữ liệu cũ khi đổi mã mới
        st.session_state['ai_context'] = {k: '' for k in st.session_state['ai_context']}
        st.session_state['chat_history'] = []
        st.rerun()
    
    st.info("💡 Mẹo: Hãy ghé thăm các trang 'Chỉ báo', 'Dòng tiền' ở menu bên trái để nạp dữ liệu cho AI.")

# 4. HÀM VẼ BIỂU ĐỒ CHUẨN TRADINGVIEW (Có nến Giờ, Ngày, Tuần)
def plot_chart(symbol, delta_days, resolution):
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=delta_days)).strftime('%Y-%m-%d')
    
    try:
        # Nếu là nến Tuần, kéo nến 1D rồi dùng Pandas gom lại cho chắc ăn, tránh API lỗi
        fetch_res = "1D" if resolution == "1W" else resolution
        
        df = stock_historical_data(
            symbol=symbol, start_date=start_date, end_date=end_date, resolution=fetch_res, type="stock"
        )
        
        if df is None or df.empty:
            st.error("Không có dữ liệu cho khoảng thời gian này.")
            return None

        # Xử lý gom nến Tuần (1W) cực kỳ mượt mà
        if resolution == "1W":
            df['time'] = pd.to_datetime(df['time'])
            df.set_index('time', inplace=True)
            df_weekly = df.resample('W-FRI').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna().reset_index()
            df = df_weekly

        # Chia 2 khung: Nến (75%) và Volume (25%)
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, 
            vertical_spacing=0.03, row_heights=[0.75, 0.25]
        )
        
        # Vẽ nến
        fig.add_trace(gr.Candlestick(
            x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], 
            name='Giá',
            increasing_line_color='#26a69a', increasing_fillcolor='#26a69a',
            decreasing_line_color='#ef5350', decreasing_fillcolor='#ef5350'
        ), row=1, col=1)
        
        # Vẽ Volume
        colors = ['#26a69a' if row['close'] >= row['open'] else '#ef5350' for index, row in df.iterrows()]
        fig.add_trace(gr.Bar(
            x=df['time'], y=df['volume'], name='Khối lượng', marker_color=colors, opacity=0.8
        ), row=2, col=1)
        
        # XỬ LÝ KHOẢNG TRỐNG THỜI GIAN
        rangebreaks = [dict(bounds=["sat", "mon"])] # Luôn cắt Thứ 7, CN
        
        # Nếu xem nến 1 Giờ, cắt thêm khoảng nghỉ đêm (15:00 hôm nay đến 09:00 sáng hôm sau)
        if resolution == "1H":
            rangebreaks.append(dict(bounds=[15, 9], pattern="hour"))

        fig.update_layout(
            title=f"<b>{symbol}</b> - Khung {resolution} (Dữ liệu {time_range})",
            title_font=dict(size=18, color='white'),
            template="plotly_dark",
            paper_bgcolor='#131722', plot_bgcolor='#131722',
            height=600, margin=dict(l=10, r=10, b=10, t=40),
            showlegend=False, xaxis_rangeslider_visible=False
        )
        
        fig.update_xaxes(rangebreaks=rangebreaks, showgrid=True, gridwidth=1, gridcolor='#2B2B43', row=1, col=1)
        fig.update_xaxes(rangebreaks=rangebreaks, showgrid=True, gridwidth=1, gridcolor='#2B2B43', row=2, col=1)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#2B2B43', row=1, col=1)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='#2B2B43', row=2, col=1)
        
        return fig
    except Exception as e:
        st.error(f"Lỗi khi vẽ biểu đồ: {e}")
        return None

# 5. GIAO DIỆN CHÍNH
st.title(f"🚀 Quant Trading Hub: {st.session_state['global_ticker']}")

col1, col2 = st.columns([6.5, 3.5])

with col1:
    with st.spinner("Đang vẽ biểu đồ..."):
        fig = plot_chart(st.session_state['global_ticker'], st.session_state['time_delta'], st.session_state['resolution'])
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

with col2:
    st.subheader("🤖 Trợ lý AI Phân Tích")
    
    context_data = st.session_state['ai_context']
    data_count = sum(1 for v in context_data.values() if v != '')
    
    if data_count == 0:
        st.warning("⚠️ AI chưa có dữ liệu. Anh hãy chọn các trang con bên trái để hệ thống quét dữ liệu trước.")
    elif data_count < 3:
        st.info(f"⚡ Đã nạp {data_count}/3 nguồn dữ liệu. Anh có thể phân tích ngay hoặc nạp thêm để chính xác hơn.")
    else:
        st.success("✅ Dữ liệu đã đầy đủ! AI sẵn sàng đưa ra nhận định chuyên sâu.")

    if st.button("🌟 Lập báo cáo phân tích chi tiết"):
        if GOOGLE_API_KEY == "DIEN_API_KEY_CUA_ANH_VAO_DAY":
            st.error("❌ Anh chưa điền API Key của Gemini ở đầu file app.py!")
        else:
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

    for message in st.session_state['chat_history']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

st.markdown("""<style>div[data-testid="stSidebarNav"] { margin-bottom: 2rem; }</style>""", unsafe_allow_html=True)
