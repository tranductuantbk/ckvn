import streamlit as st
import pandas as pd
from vnstock import stock_historical_data
from datetime import datetime, timedelta

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Bộ Lọc Cổ Phiếu", page_icon="🏆", layout="wide")

if 'global_ticker' not in st.session_state:
    st.warning("⚠️ Vui lòng quay lại Trang chủ (Bảng Điều Khiển) để khởi tạo hệ thống.")
    st.stop()

st.title("🏆 Bộ Lọc Thị Trường (Smart Screener)")
st.markdown("Quét biến động của rổ VN30 để tìm kiếm cơ hội dòng tiền và các mã thị giá đặc biệt.")

# Rổ VN30 chuẩn
VN30_TICKERS = [
    "ACB","BCM","BID","BVH","CTG","FPT","GAS","GVR","HDB","HPG",
    "MBB","MSN","MWG","PLX","POW","SAB","SHB","SSB","SSI","STB",
    "TCB","TPB","VCB","VHM","VIB","VIC","VJC","VNM","VPB","VRE"
]

# 2. HÀM TẢI DỮ LIỆU (Dùng fallback siêu ổn định thay thế cho price_board bị lỗi)
@st.cache_data(ttl=300) # Cập nhật mỗi 5 phút
def fetch_market_watch_stable(tickers):
    end_date = datetime.now().strftime('%Y-%m-%d')
    # Lấy dư ra 10 ngày để đảm bảo luôn có đủ 2 phiên giao dịch (bù trừ thứ 7, CN)
    start_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d') 
    
    results = []
    for sym in tickers:
        try:
            df = stock_historical_data(
                symbol=sym, 
                start_date=start_date, 
                end_date=end_date, 
                resolution="1D", 
                type="stock"
            )
            
            # Đảm bảo có ít nhất 2 phiên để so sánh
            if df is not None and len(df) >= 2:
                latest = df.iloc[-1]
                prev = df.iloc[-2]
                
                price = latest['close']
                volume = latest['volume']
                change_pct = ((price - prev['close']) / prev['close']) * 100
                
                results.append({
                    'Ticker': sym,
                    'Price': price,
                    'Volume': volume,
                    'Change_Pct': round(change_pct, 2)
                })
        except Exception:
            continue # Lỗi mã nào thì bỏ qua mã đó, không làm sập cả bảng
            
    if not results:
        return None, "Không lấy được dữ liệu. Sàn giao dịch có thể đang bảo trì."
        
    return pd.DataFrame(results), None

with st.spinner("Đang quét dữ liệu rổ VN30 (Việc này có thể mất 10-15 giây ở lần chạy đầu tiên)..."):
    df_market, error_msg = fetch_market_watch_stable(VN30_TICKERS)

if df_market is None or df_market.empty:
    st.error("Không thể kết nối đến bảng giá. Anh kiểm tra lại kết nối nhé.")
    if error_msg:
        st.code(f"Chi tiết:\n{error_msg}")
    st.stop()

# 3. LỌC DỮ LIỆU
top_volume = df_market.sort_values('Volume', ascending=False).head(10)
top_price_high = df_market.sort_values('Price', ascending=False).head(10)
top_price_low = df_market.sort_values('Price', ascending=True).head(10)

# 4. GIAO DIỆN HIỂN THỊ CHUYÊN NGHIỆP
tab1, tab2, tab3 = st.tabs(["🔥 Top Quan Tâm (Thanh Khoản)", "💎 Top Giá Cao", "🏷️ Top Giá Thấp"])

def render_table(df_subset, tab_name):
    st.subheader(tab_name)
    
    cols = st.columns((1, 2, 2, 2, 3))
    cols[0].markdown("**Mã CP**")
    cols[1].markdown("**Giá (VND)**")
    cols[2].markdown("**Biến động**")
    cols[3].markdown("**Khối lượng**")
    cols[4].markdown("**Hành động**")
    
    st.markdown("---")
    
    for idx, row in df_subset.iterrows():
        cols = st.columns((1, 2, 2, 2, 3))
        ticker = row['Ticker']
        
        cols[0].markdown(f"**{ticker}**")
        cols[1].markdown(f"{row['Price']:,.0f}")
        
        # Đổi màu trực quan
        color = "green" if row['Change_Pct'] > 0 else "red" if row['Change_Pct'] < 0 else "gray"
        cols[2].markdown(f"<span style='color:{color}'>{row['Change_Pct']}%</span>", unsafe_allow_html=True)
        
        cols[3].markdown(f"{row['Volume']:,.0f}")
        
        # Nút đẩy dữ liệu sang AI
        if cols[4].button(f"🧠 Gửi {ticker} cho AI", key=f"btn_{tab_name}_{ticker}"):
            st.session_state['global_ticker'] = ticker
            st.session_state['ai_context'] = {k: '' for k in st.session_state['ai_context']}
            st.session_state['chat_history'] = []
            st.success(f"Đã khóa mục tiêu {ticker}. Mời anh quay về 'Bảng Điều Khiển' (Trang chủ) để xem biểu đồ và gọi AI!")

with tab1:
    render_table(top_volume, "Top 10 Mã Được Giao Dịch Nhiều Nhất rổ VN30")
with tab2:
    render_table(top_price_high, "Top 10 Mã Có Thị Giá Cao Nhất rổ VN30")
with tab3:
    render_table(top_price_low, "Top 10 Mã Có Thị Giá Thấp Nhất rổ VN30")
