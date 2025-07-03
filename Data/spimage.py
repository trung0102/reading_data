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
    driver.maximize_window()
    driver.get(img_url) 
    window_size = driver.get_window_size()
    # width = window_size['width']
    # height = window_size['height']
    
    # print(f"Window Width: {width}px")
    # print(f"Window Height: {height}px")
    time.sleep(3)
    img = driver.find_element("tag name", "img") 
    size = img.size  # Trả về dict chứa 'width' và 'height'
    # width = size['width']
    # height = size['height']

    # print(f"Width: {width}px")
    # print(f"Height: {height}px")

    driver.save_screenshot("uploads/full_screenshot.png")
    location = img.location
    size = img.size
    image = Image.open("uploads/full_screenshot.png")
    # img_width, img_height = image.size

    # print(f"Width: {img_width}px")
    # print(f"Height: {img_height}px")
    left = location['x']
    top = location['y']
    num = 847/677
    right = left + size['width']*num
    bottom = top + size['height']*num
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

# url = "https://cms.youpass.vn/assets/" + "fa84ef8b-9264-49c9-a661-2e91edfd12da"
# img = XuliImg(url)