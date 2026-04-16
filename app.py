import gradio as gr
import pandas as pd
import time
import requests

#setting up a theme (colours)
playlist_theme = gr.themes.Base(
    primary_hue="green",
    secondary_hue="green",
    neutral_hue="gray",
).set(
    body_background_fill="#daebe0",
    body_text_color="#000000",
    button_primary_background_fill="#1DB954",
    button_primary_background_fill_hover="#1ed760",
    button_primary_text_color="#FFFFFF",
    button_secondary_background_fill="#121212",
    button_secondary_text_color="#FFFFFF",
    block_title_text_color="#1DB954",
)
#overiding previous descisions 
custom_css = """
body, .gradio-container {
    background-color: #daebe0 !important;
}
"""


playlist = []
added_count = 0
sort_keys = ["vibe", "artist", "title", "duration_sec", "added_order"]

#Fetching data from API key 
def get_song_duration_mb(title, artist):
    url = "https://musicbrainz.org/ws/2/recording/"
    headers = {"User-Agent": "PlaylistVibeMaker/1.0 ( your_email@example.com )"}
    
    params = {
        "query": f"track:{title} AND artist:{artist}",
        "fmt": "json",
        "limit": 1
    } #essentially telling it to go look for the song mentioned

    try:
        response = requests.get(url, params=params, headers=headers)
        data = response.json()

        recordings = data.get("recordings", [])
        if recordings:
            length_ms = recordings[0].get("length", 0)
            if length_ms:
                time.sleep(1)
                return length_ms // 1000

    except Exception as e:
        print("Error fetching MusicBrainz data:", e)

    return 180 #Fail safe if the song is not in API key

def add_song(title, artist, vibe):
    global added_count
    added_count += 1

    song = {
        "title": title,
        "artist": artist,
        "vibe": int(vibe),
        "duration_sec": get_song_duration_mb(title, artist),
        "added_order": added_count
    }

    playlist.append(song)
    return display_playlist(playlist)

def display_playlist(pl):
    lines = []
    for s in pl:
        lines.append(
            f"{s['title']} - {s['artist']} | Vibe: {s['vibe']} | Duration: {s['duration_sec']}"
        )
        #Display for every new song
    return "\n".join(lines)

MAX_STEPS = 900 #Fixed so that it can handle most playlists and not sacrifice efficiency

def merge_sort_steps(arr, key, steps):
    if len(arr) <= 1:
        return arr

    mid = len(arr) // 2
    left = merge_sort_steps(arr[:mid], key, steps)
    right = merge_sort_steps(arr[mid:], key, steps)

    return merge(left, right, key, steps)


def merge(left, right, key, steps):
    result = []
    i = j = 0

    while i < len(left) and j < len(right):
        if left[i][key] <= right[j][key]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1

        # Save step 
        if len(steps) < MAX_STEPS:
            steps.append(result + left[i:] + right[j:])

    result.extend(left[i:])
    result.extend(right[j:])

    if len(steps) < MAX_STEPS:
        steps.append(result.copy())

    return result

def animate_sort(key):
    speed = 0.75 #animation speed (set constant speed)

    steps = [playlist.copy()]
    sorted_list = merge_sort_steps(playlist.copy(), key, steps)

    for step in steps:
        yield display_playlist(step)
        time.sleep(speed)

    yield display_playlist(sorted_list)


with gr.Blocks(theme=playlist_theme, css=custom_css) as app:
    #attach the change of colour to the app

    with gr.Row(): #inputs (buttons, textboxes and sliders are initialized)
        title_input = gr.Textbox(label="Song Title")
        artist_input = gr.Textbox(label="Artist")
        vibe_input = gr.Slider(0, 100, step=1, label="Vibe (0–100)")
        add_button = gr.Button("Add Song")

    playlist_output = gr.Textbox(label="Playlist", lines=15)

    add_button.click(
        fn=add_song,
        inputs=[title_input, artist_input, vibe_input],
        outputs=playlist_output
    )

    with gr.Row(): #selections tools 
        sort_dropdown = gr.Dropdown(choices=sort_keys, label="Sort By")
        sort_button = gr.Button("Sort") 

    sort_button.click(
        fn=animate_sort,
        inputs=[sort_dropdown],
        outputs=playlist_output
    )

if __name__ == "__main__": 
    app.launch()