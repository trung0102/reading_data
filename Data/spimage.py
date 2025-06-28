from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from PIL import Image
import requests
import time
import os
from mimetypes import guess_extension


def XuliImg(img_url):
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(img_url) 
    time.sleep(3)
    img = driver.find_element("tag name", "img") 

    driver.save_screenshot("uploads/full_screenshot.png")
    location = img.location
    size = img.size
    image = Image.open("full_screenshot.png")
    left = location['x']
    top = location['y']
    right = left + size['width']
    bottom = top + size['height']
    image = Image.open("uploads/full_screenshot.png")
    cropped = image.crop((left, top, right, bottom))
    img_path = "uploads/cropped_image.png"
    cropped.save(img_path)
    driver.quit()

    # upload_dir = "uploads"
    # if not os.path.exists(upload_dir):
    #     os.makedirs(upload_dir)  # Tạo thư mục uploads nếu chưa tồn tại
    # content_type = response.headers.get('Content-Type', 'image/png')
    # extension = guess_extension(content_type) or '.png'
    # image_filename = os.path.join(upload_dir, f"downloaded_image{extension}")
    # with open(image_filename, "wb") as f:
    #     f.write(response.content)
    # print(f"Ảnh đã được lưu tại: {os.path.abspath(image_filename)}")

    # files = {
    #     "image": ("image.png", io.BytesIO(image_data), "image/png")
    # }
    # return files
