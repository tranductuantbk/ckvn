import streamlit as st
import pandas as pd
from vnstock import stock_historical_data
from datetime import datetime, timedelta

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Chỉ báo Kỹ thuật", page_icon="📊", layout="wide")

# Kiểm tra xem người dùng đã đi qua trang chính chưa (để có global_ticker)
if 'global_ticker' not in st.session_state:
    st.warning("⚠️ Vui lòng quay lại Trang chủ (Bảng Điều Khiển) để khởi tạo hệ thống.")
    st.stop()

ticker = st.session_state['global_ticker']
st.title(f"📊 Phân Tích Chỉ Báo Kỹ Thuật: {ticker}")

# 2. HÀM TẢI DỮ LIỆU (Có cache để ứng dụng chạy nhanh, không bị request liên tục)
@st.cache_data(ttl=900) # Lưu cache 15 phút
def get_data(symbol):
    end_date = datetime.now().strftime('%Y-%m-%d')
    # Lấy dữ liệu 6 tháng gần nhất để đủ tính MA, RSI
    start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d') 
    try:
        # Lấy dữ liệu OHLCV từ vnstock
        df = stock_historical_data(symbol, "VD", start_date, end_date, "1D", "stock")
        return df
    except Exception as e:
        return None

with st.spinner(f"Đang kéo dữ liệu OHLCV cho {ticker}..."):
    df = get_data(ticker)

if df is None or df.empty:
    st.error(f"Không thể tải dữ liệu cho mã {ticker}. Anh kiểm tra lại kết nối hoặc tên mã nhé.")
    st.stop()

# 3. TÍNH TOÁN CHỈ BÁO KỸ THUẬT (RSI & VSA)
# Tính RSI (14)
delta = df['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
df['RSI'] = 100 - (100 / (1 + rs))

# Tính Khối lượng trung bình 20 phiên để xét VSA
df['Vol_MA20'] = df['volume'].rolling(window=20).mean()

latest = df.iloc[-1]
prev = df.iloc[-2]

# Đánh giá VSA cơ bản (Biến động giá đi kèm khối lượng)
price_change = (latest['close'] - prev['close']) / prev['close'] * 100
vol_ratio = latest['volume'] / latest['Vol_MA20']

vsa_signal = "Trạng thái bình thường"
if price_change > 2 and vol_ratio > 1.5:
    vsa_signal = "Dòng tiền vào mạnh (Nỗ lực & Kết quả đồng thuận)"
elif price_change < -2 and vol_ratio > 1.5:
    vsa_signal = "Áp lực bán tháo (Phân phối)"
elif price_change > 0 and vol_ratio < 0.8:
    vsa_signal = "Tăng rướn, thiếu lực cầu (No Demand)"

# 4. HIỂN THỊ LÊN GIAO DIỆN CHUYÊN NGHIỆP
st.markdown("### 📌 Tín hiệu Phiên gần nhất")
col1, col2, col3 = st.columns(3)

col1.metric("Giá Đóng Cửa", f"{latest['close']} VND", f"{price_change:.2f}%")
col2.metric("RSI (14)", f"{latest['RSI']:.2f}", "Quá mua" if latest['RSI'] > 70 else "Quá bán" if latest['RSI'] < 30 else "Trung tính")
col3.metric("Tín hiệu VSA", vsa_signal, f"Khối lượng: {vol_ratio:.1f}x MA20", delta_color="off")

st.markdown("---")
st.subheader("Bảng Dữ Liệu Lịch Sử")
# Hiển thị 10 phiên gần nhất, đảo ngược để phiên mới nhất lên đầu
st.dataframe(df[['time', 'open', 'high', 'low', 'close', 'volume', 'RSI', 'Vol_MA20']].tail(10).iloc[::-1], use_container_width=True)

# 5. GHI DỮ LIỆU VÀO AI CONTEXT (BƯỚC QUYẾT ĐỊNH)
ai_summary = f"""
[Thông tin Chỉ báo kỹ thuật - {ticker}]
- RSI hiện tại: {latest['RSI']:.2f}.
- Đánh giá VSA: {vsa_signal}. Tỷ lệ Volume so với MA20: {vol_ratio:.1f} lần.
- Biến động giá phiên cuối: {price_change:.2f}%.
"""

# Khởi tạo an toàn phòng trường hợp chưa có
if 'ai_context' not in st.session_state:
    st.session_state['ai_context'] = {}
    
# Cập nhật thông tin vào bộ nhớ
st.session_state['ai_context']['chi_bao'] = ai_summary

st.success("✅ Đã trích xuất tín hiệu kỹ thuật và đóng gói thành công vào bộ nhớ của Quant AI Agent!")