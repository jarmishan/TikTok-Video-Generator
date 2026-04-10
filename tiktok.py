import os
import random
import time

import asyncio
import edge_tts
import numpy as np
from moviepy.editor import ImageClip, AudioFileClip, ColorClip, VideoFileClip, CompositeVideoClip, TextClip, concatenate_videoclips
from moviepy.video.fx.all import crop, resize
from moviepy.config import change_settings
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pytubefix import YouTube

from quiz import Quiz
from loadurl import load_image, load_music
from loadsongs import generate_quiz
from musicvideos import MusicVideos

change_settings({"IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"})

# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--log-level=1")
# chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values.cookies": 2})
# service = Service(executable_path="chromedriver.exe")
# driver = webdriver.Chrome(options=chrome_options, service=service)

QUIZ_SIZE = 5
QUESTIONING_LENGTH = 9
ANSWERING_LENGTH = 2
MARKING_LENGTH = 1

VOICE = 'en-US-ChristopherNeural'
OUTPUT_FILE = "assets/audio/intro.mp3"

class TikTok:
    def __init__(self, token, *, artist=None, genre=None):
        self.song_quiz = Quiz(token)

        if artist:
            self.artist_data = self.song_quiz.search_for_artist(artist)
        else:
            self.artist_data = self.song_quiz.generate_artist(genre)
        
        # (self.correct_songs, self.other_songs) = self.song_quiz.generate_quiz(QUIZ_SIZE, genre=genre, user_artist=artist)
        self.song_clips, self.correct_songs, self.other_songs= generate_quiz(self.artist_data["name"], QUIZ_SIZE)
        self.load_assets(self.artist_data, self.correct_songs)

        print(self.artist_data["name"])

        img = np.asarray(Image.open('assets/images/image.png'))
        img_array = np.reshape(img, (img.size//3, 3))
        np.sort(img_array, axis=1)
        self.COLOUR = img_array[len(img_array)//2]

        colour_i  = not bool(round(sum(self.COLOUR)/(255*3)))
        self.TEXT_COLOUR = "white" if colour_i else "black"
        self.BACK_COLOUR = [colour_i * 255] * 3
        self.font = "Century-Gothic-Bold"
        self.music_videos = MusicVideos(self.artist_data["name"])
        self.music_videos.clear()
        self.music_videos.load_videos()
        self.load_voice_over()


    def load_assets(self, artist, songs):
        artist_url = artist["images"][0]["url"]
        load_image(artist_url)
        
        # for i, (_, song_url) in enumerate(songs):
        #     load_music(song_url, str(i+1))


    def load_voice_over(self):
        TEXT = f"Guesss The Song {self.artist_data['name']} edition"

        async def amain():
            communicate = edge_tts.Communicate(TEXT, VOICE, rate="+50%")
            await communicate.save(OUTPUT_FILE)

        loop = asyncio.get_event_loop_policy().get_event_loop()

        try:
            loop.run_until_complete(amain())

        finally:
            loop.close()


    def get_music_video_clip(self):
        duration = 70
        clips = []

        for _, _, files in os.walk("assets/musicvideos"):
            for file in files:

                try:
                    clip = VideoFileClip("assets/musicvideos/"+file)

                except OSError:
                    os.remove("assets/musicvideos/"+file)
                    continue

                if clip.size[0] < clip.size[1] or "audio" in file.lower():
                    continue


                if not clip.size[1] < 1080 and not clip.size[0] < 1080 :
                    clips.append(clip)

        if not clips:
            return ColorClip(size=(540, 960), color=self.COLOUR, duration=duration), True

        length = duration / len(clips)
        cropped_clips = []

        for clip in clips:
            upper_bound = int(0.75*(clip.duration-length))
            lower_bound = int(0.25*(clip.duration-length))
            start = random.randint(lower_bound, upper_bound)

            cropped_clip = crop(clip,  x_center=960 , y_center=540, width=540, height=960)
            cropped_clips.append(cropped_clip.subclip(start, start+length))

        return concatenate_videoclips(cropped_clips), False


    def get_intro_scene(self, music_video_clip):
        intro_audio_clip = AudioFileClip("assets/audio/intro.mp3")
        duration = int(intro_audio_clip.duration)+1


        bg = music_video_clip.subclip(0, duration)
        back = ColorClip(size=(410, 410), color=self.BACK_COLOUR, duration=duration
                        ).set_position(lambda _: (65, 97))

        artist_img= ImageClip("assets/images/image.png", duration=duration
                        ).set_position(lambda _: (70, 103)
                        ).resize((400, 400))

        title = TextClip(f"Guess the song\n\nedition", fontsize=40, color=self.TEXT_COLOUR, font=self.font
                        ).set_position(("center", 545)
                        ).set_duration(duration)

        artist_name =  TextClip(f"{self.artist_data['name']}", fontsize=55, color=self.TEXT_COLOUR, font=self.font
                        ).set_position(("center", 589)
                        ).set_duration(duration)

        intro_video_clip = CompositeVideoClip([bg, back, artist_img, artist_name, title])
        intro_video_clip.audio = intro_audio_clip
        intro_video_clip.speedx(2)

        return intro_video_clip


    def get_quiz_scene(self, music_video_clip, intro_length):
        bg_count = intro_length

        def get_base(duration, start):
            return [
                music_video_clip.subclip(start, start+duration),
                ColorClip(size=(330, 330), color=self.BACK_COLOUR, duration=duration).set_position(lambda _: (105, 77)),
                ImageClip("assets/images/image.png", duration=duration).set_position(lambda _: (110, 82)).resize((320, 320)),
                ImageClip("assets/images/choices.png", duration=duration).set_position(lambda _: (71, 550))
            ]

        tick_sound = AudioFileClip(f"assets/audio/clock.mp3").subclip(0, 2)
        correct_sound = AudioFileClip(f"assets/audio/correct.mp3").subclip(0, 1)

        questions = []

        for i in range(QUIZ_SIZE):
            correct = self.correct_songs[i]
            incorrect  = self.other_songs[i*2:(i+1)*2]
            all_songs = incorrect + [correct]
            random.shuffle(all_songs)

            correct_index = all_songs.index(correct)

            def get_options(duration):
                options = []

                for j in range(3):
                    options.append(
                        TextClip(f"{all_songs[j]}", fontsize=30, color="BLACK", font=self.font
                            ).set_position((90, 563+94*j)
                            ).set_duration(duration)
                    )

                return options

            song = self.song_clips[i]
            questioning_clip = CompositeVideoClip(get_base(QUESTIONING_LENGTH, bg_count) + get_options(QUESTIONING_LENGTH))
            questioning_clip.audio = song
            bg_count += QUESTIONING_LENGTH

            answering_clip = CompositeVideoClip(get_base(ANSWERING_LENGTH, bg_count) + get_options(ANSWERING_LENGTH))
            answering_clip.audio = tick_sound
            bg_count += ANSWERING_LENGTH

            marking_clip = CompositeVideoClip(
                get_base(MARKING_LENGTH, bg_count) +
                [ColorClip(size=(389, 58), color=(100, 255, 100), duration=MARKING_LENGTH).set_position(("center", 554+95*correct_index))] +
                get_options(MARKING_LENGTH))

            marking_clip.audio = correct_sound
            bg_count += MARKING_LENGTH

            final_clip = concatenate_videoclips([questioning_clip, answering_clip, marking_clip])

            questions.append(
                final_clip
            )

        audio_clip = concatenate_videoclips(questions)
        return audio_clip


    def make_video(self):
        music_video_clip, failed = self.get_music_video_clip()
        intro_clip = self.get_intro_scene(music_video_clip)
        quiz_clip = self.get_quiz_scene(music_video_clip, intro_clip.duration)

        if failed:
            quiz_clip.fps = 1
            intro_clip.fps = 1

        final_video = concatenate_videoclips([intro_clip, quiz_clip])
        final_video.write_videofile(f"videos/tiktok{len(os.listdir('videos'))}.mp4")


        make_hastag = lambda name: name.replace(" ", "").lower()
        f = open("hashtag.txt", "a")
        f.write(f"{self.artist_data['name']} Song quiz. Comment down your score!\n",)
        f.write(f"#{make_hastag(self.artist_data['name'])} #music #guessthesong #fyp\n\n")
        f.close()