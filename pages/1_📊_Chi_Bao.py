import streamlit as st
import pandas as pd
from vnstock import stock_historical_data
from datetime import datetime, timedelta

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Chỉ báo Kỹ thuật", page_icon="📊", layout="wide")

if 'global_ticker' not in st.session_state:
    st.warning("⚠️ Vui lòng quay lại Trang chủ (Bảng Điều Khiển) để khởi tạo hệ thống.")
    st.stop()

ticker = st.session_state['global_ticker']
st.title(f"📊 Phân Tích Chỉ Báo Kỹ Thuật: {ticker}")

# 2. HÀM TẢI DỮ LIỆU (Đã đổi tên thành v2 để ép Streamlit xóa cache cũ)
@st.cache_data(ttl=900) 
def fetch_technical_data_v2(symbol):
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d') 
    try:
        df = stock_historical_data(symbol=symbol, start_date=start_date, end_date=end_date, resolution="1D", type="stock")
        return df, None
    except Exception as e:
        return None, str(e) # Trả về lỗi chi tiết thay vì giấu đi

with st.spinner(f"Đang kéo dữ liệu OHLCV cho {ticker}..."):
    df, error_msg = fetch_technical_data_v2(ticker)

if df is None or df.empty:
    st.error(f"Không thể tải dữ liệu cho mã {ticker}.")
    if error_msg:
        st.code(f"Mã lỗi hệ thống (Chụp ảnh màn hình này cho em nếu vẫn lỗi nhé):\n{error_msg}")
    st.stop()

# 3. TÍNH TOÁN CHỈ BÁO KỸ THUẬT
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

df['Vol_MA20'] = df['volume'].rolling(window=20).mean()

latest = df.iloc[-1]
prev = df.iloc[-2]

price_change = (latest['close'] - prev['close']) / prev['close'] * 100
vol_ratio = latest['volume'] / latest['Vol_MA20']

vsa_signal = "Trạng thái bình thường"
if price_change > 2 and vol_ratio > 1.5:
    vsa_signal = "Dòng tiền vào mạnh (Nỗ lực & Kết quả đồng thuận)"
elif price_change < -2 and vol_ratio > 1.5:
    vsa_signal = "Áp lực bán tháo (Phân phối)"
elif price_change > 0 and vol_ratio < 0.8:
    vsa_signal = "Tăng rướn, thiếu lực cầu (No Demand)"

# 4. HIỂN THỊ LÊN GIAO DIỆN
st.markdown("### 📌 Tín hiệu Phiên gần nhất")
col1, col2, col3 = st.columns(3)

col1.metric("Giá Đóng Cửa", f"{latest['close']} VND", f"{price_change:.2f}%")
col2.metric("RSI (14)", f"{latest['RSI']:.2f}", "Quá mua" if latest['RSI'] > 70 else "Quá bán" if latest['RSI'] < 30 else "Trung tính")
col3.metric("Tín hiệu VSA", vsa_signal, f"Khối lượng: {vol_ratio:.1f}x MA20", delta_color="off")

st.markdown("---")
st.subheader("Bảng Dữ Liệu Lịch Sử")
st.dataframe(df[['time', 'open', 'high', 'low', 'close', 'volume', 'RSI', 'Vol_MA20']].tail(10).iloc[::-1], use_container_width=True)

# 5. GHI DỮ LIỆU VÀO AI CONTEXT
ai_summary = f"""
[Thông tin Chỉ báo kỹ thuật - {ticker}]
- RSI hiện tại: {latest['RSI']:.2f}.
- Đánh giá VSA: {vsa_signal}. Tỷ lệ Volume so với MA20: {vol_ratio:.1f} lần.
- Biến động giá phiên cuối: {price_change:.2f}%.
"""

if 'ai_context' not in st.session_state:
    st.session_state['ai_context'] = {}
    
st.session_state['ai_context']['chi_bao'] = ai_summary

st.success("✅ Đã trích xuất tín hiệu kỹ thuật và đóng gói thành công vào bộ nhớ của Quant AI Agent!")
