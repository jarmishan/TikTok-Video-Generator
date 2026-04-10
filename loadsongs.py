import time
import random

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pytubefix import YouTube
from moviepy.editor import  AudioFileClip

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--log-level=1")
chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.cookies": 2})
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(options=chrome_options, service=service)


def get_channel_id(artist):
    driver.get(f"https://music.youtube.com/search?q={artist}")

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, artist))
    )
    artist_page_link = driver.find_element(By.PARTIAL_LINK_TEXT, artist)
    artist_page_link.click()

    time.sleep(2)

    channel_id = driver.current_url.split('/')[-1]

    return channel_id


def generate_quiz(artist, quiz_size):
    urls = []
    correct_song_names = []
    incorrect_song_names = []
    song_clips = []

    channel_id = get_channel_id(artist)
    driver.get(f"https://music.youtube.com/channel/{channel_id}")

    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Songs"))
    )
    link = driver.find_element(By.PARTIAL_LINK_TEXT, "Songs")
    link.click()

    time.sleep(1)

    elements = driver.find_elements(By.XPATH, "//*[@href]")

    for element in elements:
        url = element.get_attribute("href")

        if "https://music.youtube.com/watch?v=" in url:
            urls.append(url)

    driver.quit()

    songs = random.sample(urls, quiz_size*3)
    correct_songs = songs[:quiz_size]
    incorrect_songs = songs[quiz_size:]

    for song in incorrect_songs:
        yt = YouTube(song)
        video = yt.streams.filter(only_audio=True).first()
        title = video.title.split(".")[0]
        if len(title) >= 23:
            title = title[:20]+"..."

        incorrect_song_names.append(title)
    
    for song in correct_songs:
        yt = YouTube(song)
        video = yt.streams.filter(only_audio=True).first()
        title = video.title.split(".")[0]
        if len(title) >= 23:
            title = title[:20]+"..."

        correct_song_names.append(title)

    for song in correct_songs:
        yt = YouTube(song)
        video = yt.streams.filter(only_audio=True).first().download()
        title = video.title().split(".")[0]
        song_clip = AudioFileClip(f"{title}.mp4")
        length = song_clip.duration
        
        start = int(0.25*length)

        song_clips.append(song_clip.subclip(start, start+9))

    return song_clips, correct_song_names, incorrect_song_names

