import streamlit as st
import pandas as pd
import numpy as np
from vnstock import stock_historical_data
from datetime import datetime, timedelta

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Dòng Tiền Cá Mập", page_icon="🦈", layout="wide")

if 'global_ticker' not in st.session_state:
    st.warning("⚠️ Vui lòng quay lại Trang chủ (Bảng Điều Khiển) để khởi tạo hệ thống.")
    st.stop()

ticker = st.session_state['global_ticker']
st.title(f"🦈 Theo Dấu Dòng Tiền Lớn (Smart Money): {ticker}")
st.markdown("Phân tích áp lực Mua/Bán chủ động và sự dịch chuyển của dòng tiền qua chỉ báo OBV (On-Balance Volume).")

# 2. TẢI DỮ LIỆU (Đã đổi tên hàm thành v2 để xóa cache cũ, và in ra lỗi thật)
@st.cache_data(ttl=900)
def fetch_money_flow_data_v2(symbol):
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    try:
        df = stock_historical_data(symbol=symbol, start_date=start_date, end_date=end_date, resolution="1D", type="stock")
        return df, None
    except Exception as e:
        return None, str(e)

with st.spinner(f"Đang dò tìm dấu vết dòng tiền cho {ticker}..."):
    df, error_msg = fetch_money_flow_data_v2(ticker)

if df is None or df.empty:
    st.error("Không thể tải dữ liệu. Vui lòng kiểm tra lại kết nối.")
    if error_msg:
        st.code(f"Mã lỗi chi tiết:\n{error_msg}")
    st.stop()

# 3. TÍNH TOÁN DÒNG TIỀN (Chỉ báo OBV)
df['Price_Diff'] = df['close'].diff()
df['Direction'] = np.where(df['Price_Diff'] > 0, 1, np.where(df['Price_Diff'] < 0, -1, 0))
df['OBV'] = (df['Direction'] * df['volume']).cumsum()

recent_obv_trend = df['OBV'].iloc[-1] - df['OBV'].iloc[-5]
price_trend = df['close'].iloc[-1] - df['close'].iloc[-5]

if recent_obv_trend > 0 and price_trend > 0:
    trend_status = "Dòng tiền VÀO mạnh (Đồng thuận tăng)"
elif recent_obv_trend > 0 and price_trend <= 0:
    trend_status = "Đang GOM HÀNG ngầm (Phân kỳ dương OBV)"
elif recent_obv_trend < 0 and price_trend < 0:
    trend_status = "Dòng tiền RÚT RA (Đồng thuận giảm)"
else:
    trend_status = "Đang PHÂN PHỐI ngầm (Phân kỳ âm OBV)"

# 4. HIỂN THỊ GIAO DIỆN
st.subheader("1. Tổng quan Dòng Tiền (5 Phiên gần nhất)")
col1, col2 = st.columns(2)

col1.metric(
    "Trạng thái Smart Money", 
    trend_status, 
    f"{recent_obv_trend:,.0f} Vol (Chênh lệch Mua/Bán)", 
    delta_color="normal" if recent_obv_trend > 0 else "inverse"
)

st.markdown("---")
st.subheader("2. Biểu đồ Tích lũy OBV (3 tháng)")
st.info("💡 Mẹo: Nhìn vào biểu đồ này. Nếu giá cổ phiếu đi ngang nhưng đường OBV dốc lên, tay to đang gom hàng chuẩn bị đánh lên.")

chart_data = df.set_index('time')[['OBV']]
st.line_chart(chart_data)

# 5. ĐÓNG GÓI DỮ LIỆU CHO AI AGENT
ai_summary = f"""
[Thông tin Dòng Tiền - {ticker}]
- Trạng thái Smart Money (dựa trên OBV 5 phiên): {trend_status}.
- Chênh lệch khối lượng Mua/Bán ròng: {recent_obv_trend:,.0f} cổ phiếu.
"""

if 'ai_context' not in st.session_state:
    st.session_state['ai_context'] = {}
    
st.session_state['ai_context']['dong_tien'] = ai_summary

st.success("✅ Đã cập nhật thành công hành vi của Dòng tiền lớn vào bộ nhớ AI!")
