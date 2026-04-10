import os
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytubefix.exceptions
from pytubefix import Playlist, YouTube

class MusicVideos:
    def __init__(self, artist):
        self.artist = artist

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--log-level=1")
        chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.cookies": 2})
        service = Service(executable_path="chromedriver.exe")
        self.driver = webdriver.Chrome(options=chrome_options, service=service)

        self.urls = []

    def _filter_name(self, name):
        return name.lower().replace(" ", "")

    def _get_channel_id(self):
        self.driver.get(f"https://music.youtube.com/search?q={self._filter_name(self.artist)}")

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, self.artist))
        )
        artist_page_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, self.artist)
        artist_page_link.click()

        time.sleep(2)

        channel_id = self.driver.current_url.split('/')[-1]

        return channel_id


    def _get_urls(self):
        channel_id = self._get_channel_id()

        self.driver.get(f"https://music.youtube.com/channel/{channel_id}")

        WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Videos"))
        )
        link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "Videos")
        link.click()

        time.sleep(1)

        elems = self.driver.find_elements(By.XPATH, "//*[@href]")

        self.urls = []

        for elem in elems:
            url = elem.get_attribute("href")

            if "https://music.youtube.com/watch?v=" in url:
                self.urls.append(url)

        self.driver.quit()


    def load_videos(self):
        self._get_urls()

        random.shuffle(self.urls)
        length = min(5, len(self.urls))
        count = 0
        print("downloading...")

        for i, url in enumerate(self.urls):
            if count > length:
                break

            vid = YouTube(url)
            # print(url)
            if "audio" not in vid.title.lower() and "lyric" not in vid.title.lower():
                try:
                    vid.streams.filter(res="1080p").first().download("assets/musicvideos")
                    count += 1
                except:
                    pass #print("1")



        print("finished downloading")

    def clear(self):
        for _, _, files in os.walk("assets/musicvideos"):
            for file in files:
                os.remove("assets/musicvideos/"+file)