from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

import pandas as pd
import time
import datetime
import re

import pyautogui

options = ChromeOptions()
user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
options.add_argument(f"--user-agent={user_agent}")
options.add_argument("--lang=ko_KR")

service = ChromeService(executable_path=ChromeDriverManager().install())

driver = webdriver.Chrome(service=service, options=options)



url_df = pd.read_csv("../steam.csv")

reviews = []

for i, url in enumerate(list(url_df["reviewlinks"][:335])):
    print(url[:-24])

    driver.get(url[:-24])
    time.sleep(0.5)

    pyautogui.hotkey("shift", "f10")
    pyautogui.hotkey("t")

    time.sleep(1)

    for k in range(27):
        print(f"\rscrolling {k+1}", end="")
        driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")  # 스크롤 내리는 동작
        time.sleep(1)

    print("\rend scroll")

    review = ""

    reviews_temp = driver.find_elements(By.CLASS_NAME, "apphub_CardTextContent")

    print(f"리뷰 개수 : {len(reviews_temp)}")

    for j in range(len(reviews_temp)):
        target_review = reviews_temp[j].text

        cleand_review = re.sub("[^가-힣]", " ", target_review)

        review = review + " " + cleand_review.strip()

    # for j in range(1, 201):
    #
    #     print(f"\r{j}/200", end="")
    #
    #     review_xpath = f'//*[@id="page_1_row_1_template_twoSmall"]/div[{j}]/div[1]/div[1]/div[3]'
    #
    #     try:
    #         review_text = driver.find_element(By.XPATH, review_xpath).text
    #
    #         review_text = re.sub("[^가-힣]", " ", review_text)
    #
    #         review = review + " " + review_text
    #
    #     except:
    #         pass

    print(f"{review}")

    reviews.append(review)

print(f"개임 리뷰 총 개수 {len(reviews)}")

temp_df = pd.DataFrame({"titles": url_df["reviewlinks"][:335], "reviews": reviews})
temp_df.to_csv(f"../review_data_0_334.csv", index=False)