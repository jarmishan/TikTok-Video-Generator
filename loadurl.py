from requests import get

def load_image(img_url):
    img = f'assets/images/image.png'
    request = get(img_url, stream=True)

    with open(img, 'wb') as f:
        for block in request.iter_content(1024):
            f.write(block)
            
            
def load_music(song_url, song_name):
    request = get(song_url, stream=True)
    song = f'assets/songs/{song_name}.mp3'
    
    with open(song, 'wb') as f:
        for block in request.iter_content(1024):
            f.write(block)