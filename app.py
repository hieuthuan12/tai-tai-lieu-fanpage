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
    options.add_argument('--headless') # Chạy ngầm
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    
    # 1. Thêm "mặt nạ" giả làm điện thoại iPhone để lách tường lửa đăng nhập
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1')
    
    # 2. Đổi link sang bản Mobile để web nhẹ và dễ trích xuất dữ liệu hơn
    if "facebook.com" in url:
         url = url.replace("www.facebook.com", "m.facebook.com")

    # Khởi tạo trình duyệt
    try:
        options.binary_location = "/usr/bin/chromium"
        driver = webdriver.Chrome(options=options)
    except Exception:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
    driver.get(url)
    
    # 3. Tăng thời gian chờ lên 8 giây để vượt qua độ trễ mạng của máy chủ
    time.sleep(8) 
    
    # 4. Trượt trang xuống dưới để Facebook ép tải các ảnh đang bị ẩn
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(3)
    
    # Thu thập ảnh
    images = driver.find_elements(By.TAG_NAME, 'img')
    
    img_urls = []
    for img in images:
        src = img.get_attribute('src')
        # Lọc lấy ảnh thật (chứa scontent)
        if src and "scontent" in src:
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
            if img.mode != 'RGB':
                img = img.convert('RGB')
            image_list.append(img)
        except Exception as e:
            st.error(f"Lỗi tải ảnh: {e}")
            
    if image_list:
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
                st.warning("Không tìm thấy hình ảnh tài liệu nào. Bài viết có thể bị giới hạn quyền riêng tư.")
    else:
        st.error("Vui lòng nhập link bài viết Fanpage!")
