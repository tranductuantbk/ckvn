import streamlit as st
import pandas as pd
from vnstock import price_board

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="Bộ Lọc Cổ Phiếu", page_icon="🏆", layout="wide")

if 'global_ticker' not in st.session_state:
    st.warning("⚠️ Vui lòng quay lại Trang chủ (Bảng Điều Khiển) để khởi tạo hệ thống.")
    st.stop()

st.title("🏆 Bộ Lọc Thị Trường (Smart Screener)")
st.markdown("Quét biến động realtime của rổ VN30 để tìm kiếm cơ hội dòng tiền và các mã thị giá đặc biệt.")

# Danh sách VN30 để tối ưu tốc độ quét
VN30_TICKERS = "ACB,BCM,BID,BVH,CTG,FPT,GAS,GVR,HDB,HPG,MBB,MSN,MWG,PLX,POW,SAB,SHB,SSB,SSI,STB,TCB,TPB,VCB,VHM,VIB,VIC,VJC,VNM,VPB,VRE"

# 2. HÀM TẢI DỮ LIỆU BẢNG GIÁ
@st.cache_data(ttl=60) # Cập nhật mỗi 1 phút
def fetch_market_watch(tickers):
    try:
        df = price_board(tickers)
        
        # Trích xuất các cột quan trọng
        # vnstock 0.2.8 trả về các cột: 'Mã CP', 'Khớp lệnh_Giá', 'Tổng KL', 'Khớp lệnh_%'
        df_clean = df[['Mã CP', 'Khớp lệnh_Giá', 'Tổng KL', 'Khớp lệnh_%']].copy()
        df_clean.columns = ['Ticker', 'Price', 'Volume', 'Change_Pct']
        
        # Xử lý dữ liệu số (Loại bỏ lỗi nếu có chữ cái lọt vào)
        df_clean['Price'] = pd.to_numeric(df_clean['Price'], errors='coerce')
        df_clean['Volume'] = pd.to_numeric(df_clean['Volume'], errors='coerce') * 10 
        df_clean['Change_Pct'] = pd.to_numeric(df_clean['Change_Pct'], errors='coerce')
        
        return df_clean.dropna(), None
    except Exception as e:
        return None, str(e)

with st.spinner("Đang quét bảng giá realtime VN30..."):
    df_market, error_msg = fetch_market_watch(VN30_TICKERS)

if df_market is None or df_market.empty:
    st.error("Không thể kết nối đến bảng giá realtime. Anh kiểm tra lại kết nối nhé.")
    if error_msg:
        st.code(f"Mã lỗi:\n{error_msg}")
    st.stop()

# 3. LỌC DỮ LIỆU
# Lấy Top 10 Thanh khoản (Được quan tâm nhất)
top_volume = df_market.sort_values('Volume', ascending=False).head(10)
# Lấy Top 10 Giá cao nhất
top_price_high = df_market.sort_values('Price', ascending=False).head(10)
# Lấy Top 10 Giá thấp nhất
top_price_low = df_market.sort_values('Price', ascending=True).head(10)

# 4. GIAO DIỆN HIỂN THỊ CHUYÊN NGHIỆP
tab1, tab2, tab3 = st.tabs(["🔥 Top Quan Tâm (Thanh Khoản)", "💎 Top Giá Cao", "🏷️ Top Giá Thấp"])

# Hàm tạo bảng hiển thị kèm nút bấm điều hướng
def render_table(df_subset, tab_name):
    st.subheader(tab_name)
    
    # Chia cột để làm giao diện đẹp hơn
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
        
        # Tô màu xanh/đỏ cho biến động
        color = "green" if row['Change_Pct'] > 0 else "red" if row['Change_Pct'] < 0 else "gray"
        cols[2].markdown(f"<span style='color:{color}'>{row['Change_Pct']}%</span>", unsafe_allow_html=True)
        
        cols[3].markdown(f"{row['Volume']:,.0f}")
        
        # NÚT BẤM KỲ DIỆU: Đổi mã và quay về trang chủ
        if cols[4].button(f"🧠 Gửi {ticker} cho AI", key=f"btn_{tab_name}_{ticker}"):
            st.session_state['global_ticker'] = ticker
            # Reset lại bộ nhớ AI cho mã mới
            st.session_state['ai_context'] = {k: '' for k in st.session_state['ai_context']}
            st.session_state['chat_history'] = []
            st.success(f"Đã chuyển mục tiêu sang {ticker}. Anh hãy mở menu bên trái và chọn 'Trang Chủ' để xem biểu đồ nhé!")

with tab1:
    render_table(top_volume, "Top 10 Mã Được Giao Dịch Nhiều Nhất")

with tab2:
    render_table(top_price_high, "Top 10 Mã Có Thị Giá Cao Nhất")

with tab3:
    render_table(top_price_low, "Top 10 Mã Có Thị Giá Thấp Nhất")