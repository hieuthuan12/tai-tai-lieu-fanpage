import streamlit as st
import time
import requests
from io import BytesIO
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By

# Cấu hình giao diện Web
st.set_page_config(page_title="Trình tải tài liệu Fanpage sang PDF", layout="centered")
st.title("📥 Tool Tải Ảnh Fanpage -> PDF")

# Lấy link từ người dùng
url = st.text_input("Dán đường link bài viết Fanpage chứa ảnh vào đây:")

def get_images_from_fb(url):
    """Sử dụng Selenium để giả lập trình duyệt và lấy link ảnh"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless') # Chạy ngầm, không mở cửa sổ trình duyệt
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    # Khởi tạo trình duyệt (Tự động thích ứng máy cục bộ và Cloud)
try:
    # Cấu hình dành cho khi chạy trên Cloud (Linux)
    options.binary_location = "/usr/bin/chromium"
    driver = webdriver.Chrome(options=options)
except Exception:
    # Cấu hình dành cho khi chạy dưới máy cá nhân (Windows)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(url)
    
    # Đợi Facebook tải trang (có thể tăng thời gian nếu mạng chậm)
    time.sleep(5) 
    
    # Tìm các thẻ chứa hình ảnh (Lưu ý: Class của Facebook thường xuyên thay đổi)
    # Đây là logic mẫu, bạn cần F12 trên FB để tìm thẻ img chính xác chứa tài liệu
    images = driver.find_elements(By.TAG_NAME, 'img')
    
    img_urls = []
    for img in images:
        src = img.get_attribute('src')
        if src and "scontent" in src: # Lọc các link ảnh thực tế của FB
            img_urls.append(src)
            
    driver.quit()
    return img_urls

def create_pdf(img_urls):
    """Tải ảnh từ link và nối thành PDF"""
    image_list = []
    for img_url in img_urls:
        try:
            response = requests.get(img_url)
            img = Image.open(BytesIO(response.content))
            # Chuyển đổi sang hệ màu RGB để tránh lỗi khi lưu PDF
            if img.mode != 'RGB':
                img = img.convert('RGB')
            image_list.append(img)
        except Exception as e:
            st.error(f"Lỗi tải ảnh: {e}")
            
    if image_list:
        # Tạo file PDF trên bộ nhớ tạm
        pdf_bytes = BytesIO()
        image_list[0].save(pdf_bytes, format='PDF', save_all=True, append_images=image_list[1:])
        return pdf_bytes.getvalue()
    return None

# Xử lý khi nhấn nút
if st.button("Tải xuống và Tạo PDF"):
    if url:
        with st.spinner("Đang quét Fanpage và trích xuất tài liệu (quá trình này có thể mất vài phút)..."):
            urls = get_images_from_fb(url)
            
            if urls:
                st.success(f"Đã tìm thấy {len(urls)} trang tài liệu. Đang đóng gói thành PDF...")
                pdf_data = create_pdf(urls)
                
                if pdf_data:
                    st.download_button(
                        label="⬇️ Tải file PDF về máy",
                        data=pdf_data,
                        file_name="TaiLieu_Fanpage.pdf",
                        mime="application/pdf"
                    )
            else:
                st.warning("Không tìm thấy hình ảnh tài liệu nào. Bài viết có thể bị giới hạn quyền riêng tư hoặc cấu trúc Facebook đã thay đổi.")
    else:
        st.error("Vui lòng nhập link bài viết Fanpage!")
