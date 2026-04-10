import json
import random

import numpy as np
from requests import get

BASE_URL = "https://api.spotify.com/v1/"

class Quiz:
    def __init__(self, token): 
        self.token = token
        self.auth_header = {"Authorization": "Bearer " + self.token}

    def search_for_artist(self, artist_name):
        url = BASE_URL+"search"
        query= f"?q={artist_name}&type=artist&limit=1"
        
        query_url = url + query
        result = get(query_url, headers=self.auth_header)
        json_result = json.loads(result.content)["artists"]["items"]
        
        return json_result[0]
    
    def _get_albums(self, artist_id):
        url = BASE_URL+f"artists/{artist_id}/albums"
        result = get(url, headers=self.auth_header)
        json_result = json.loads(result.content)["items"]
        
        return json_result

    def get_album_tracks(self, album_id):
        url = BASE_URL+f"albums/{album_id}/tracks?country=US"
        result = get(url, headers=self.auth_header)
        json_result = json.loads(result.content)["items"]
        
        return json_result   
    
    def generate_artist(self, genre):
        filtered_genre = genre.replace(" ", "%20").replace("&", "%26")

        while True:
            letter = random.choice("abcdefghijklmnopqrstuvwxyz")
            offset = int(min(np.abs(np.round(np.random.normal(1, 125, 1)))[0], 1000))
            id = f"{letter}{offset}\n"
            query = f"?q=genre:%22{filtered_genre}%22&type=artist&offset={offset}&market=US&limit=1"
            url = BASE_URL+"search"
            
            query_url = url + query
            result = get(query_url, headers=self.auth_header)
            
            json_result = json.loads(result.content)   
            print(json_result)
            artists = json_result["artists"]["items"]
            f = open(f"removed\hip%20hop.txt",  "r+")
        
            removed = f.readlines()

            if artists and id not in removed:
                artist = artists[0]

                if artist["popularity"] >= 74:
                    f.close()
    
                    return artist
                
                f.write(id)
                f.close()


    def generate_quiz(self, quiz_size, genre=None, user_artist=None):
        while True:
            artist = user_artist
            if not user_artist:   
                artist = self.generate_artist(genre)
        
            artist_info = self._search_for_artist(artist)
            artist_id = artist_info["id"]

            genres = artist_info["genres"]
            if "tin" in genres or "desi" in genres:
                continue

            valid_songs = []
            all_songs = []
            versions = ["version", "sped", "slowed", "remix", "live"]
            
            for album in self._get_albums(artist_id):
                record = self._get_album_tracks(album["id"])

                for song in record:
                    artists_names = song["artists"]
                    
                    if artist in [artists_names[i]['name'] for i in range(len(artists_names))] and all([version not in song['name'].lower() for version in versions]) and (not all_songs or all_songs[-1] not in song['name']) and len(song['name']) <= 23:
    
                        if song.get('preview_url') and song['name'] not in all_songs:
                            valid_songs.append([song['name'], song['preview_url']])
                    
                        all_songs.append(song['name'])
                        
            if len(valid_songs) >= quiz_size:
                break    
                
        random.shuffle(valid_songs)
        correct_songs = valid_songs[:quiz_size]
        
        incorrect_songs = list(set(all_songs) - set(s for s, _ in correct_songs))
        random.shuffle(incorrect_songs)
        

        return artist_info, [correct_songs, incorrect_songs[:quiz_size*2]]