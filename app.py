import streamlit as st

# 1. CẤU HÌNH TRANG (Phải luôn nằm đầu tiên)
st.set_page_config(
    page_title="Quant Trading Hub",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. KHỞI TẠO BỘ NHỚ DÙNG CHUNG (Session State)
# Điều này cực kỳ quan trọng để AI đọc được data từ các trang khác
if 'global_ticker' not in st.session_state:
    st.session_state['global_ticker'] = 'SSI' # Mặc định

if 'ai_context' not in st.session_state:
    st.session_state['ai_context'] = {
        'chi_bao': '',
        'dong_tien': '',
        'tin_tuc': ''
    }

if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []

# 3. THANH ĐIỀU HƯỚNG BÊN TRÁI (Sidebar - Áp dụng toàn cục)
with st.sidebar:
    st.title("⚙️ Bảng Điều Khiển")
    st.markdown("---")
    
    # Input mã chứng khoán. Khi đổi ở đây, toàn bộ các trang con sẽ cập nhật theo
    new_ticker = st.text_input("Nhập mã Cổ phiếu (VD: SSI, HPG):", value=st.session_state['global_ticker']).upper()
    if new_ticker != st.session_state['global_ticker']:
        st.session_state['global_ticker'] = new_ticker
        # Reset bối cảnh AI khi đổi mã
        st.session_state['ai_context'] = {k: '' for k in st.session_state['ai_context']}
        st.rerun()

    st.selectbox("Khung thời gian (Sắp ra mắt):", ['1D', '1W', '1M', '1m', '5m'], index=0, disabled=True)

# 4. GIAO DIỆN TRANG CHÍNH (Main Dashboard)
st.title(f"📊 Phân Tích Tổng Quan: {st.session_state['global_ticker']}")
st.markdown("Hệ thống tổng hợp dữ liệu từ các module và AI đánh giá.")

# Chia đôi màn hình: Biểu đồ (Trái) & Trợ lý AI (Phải)
col1, col2 = st.columns([6, 4])

with col1:
    st.subheader("Biểu đồ Kỹ thuật")
    st.info("Khu vực này sẽ nhúng biểu đồ Plotly tĩnh hoặc Lightweight-charts ở các bước sau.")
    # Placeholder cho biểu đồ
    st.empty() 

with col2:
    st.subheader("🤖 Quant AI Agent")
    st.markdown("*AI đang đọc dữ liệu từ các trang con...*")
    
    # Hiển thị trạng thái dữ liệu đã thu thập được
    with st.expander("🔍 Xem dữ liệu AI đang nắm giữ"):
        st.json(st.session_state['ai_context'])
    
    # Giao diện Chat
    st.markdown("---")
    for message in st.session_state['chat_history']:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Hỏi AI về mã này..."):
        # Lưu câu hỏi
        st.session_state['chat_history'].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Giả lập AI trả lời (Sẽ tích hợp API thật sau)
        with st.chat_message("assistant"):
            response = f"Dựa trên bối cảnh hệ thống thu thập được, đây là phân tích về {st.session_state['global_ticker']}..."
            st.markdown(response)
            st.session_state['chat_history'].append({"role": "assistant", "content": response})