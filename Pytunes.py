from tkinter import *
import pygame
import numpy as np
import pyaudio
from pydub import AudioSegment
import os
import glob
import threading
import time
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

# Initialize the root window
root = Tk()
root.title('PyTunes')
root.iconbitmap(r'C:\Users\Asus\Downloads\Pytunes.ico')
root.geometry("600x500")


# Initialize the mixer module in pygame
pygame.init()


WIDTH, HEIGHT = 1400, 520

# Colors
BLACK = (0, 0, 0)
BAR_COLOR = (0, 255, 128)

# Frame for the visualizer within the Tkinter window
visualizer_frame = tk.Frame(root, width=WIDTH, height=HEIGHT)
visualizer_frame.pack(pady=20)

# Create an embedded Pygame surface inside the Tkinter window
embed = tk.Canvas(visualizer_frame, width=WIDTH, height=HEIGHT,bg = "black")
embed.pack()


# Embed Pygame inside Tkinter
os.environ['SDL_WINDOWID'] = str(embed.winfo_id())
os.environ['SDL_VIDEODRIVER'] = 'windib'


screen = pygame.display.set_mode((WIDTH, HEIGHT))


# Initialize PyAudio
p = pyaudio.PyAudio()


playlist = glob.glob(r"C:\Users\Asus\Desktop\Programing tools\Project\Mobile files\Songs\*.mp3")


current_song_index = 0


#This is for the music progress bar
def update_progress():
    total_length = pygame.mixer.Sound(song_path).get_length()  # Get the total song length
    progress_canvas.config(width=progress_width)  # Set the width of the canvas
    progress_bar_rect = (0, 0, progress_width, progress_height)  # Define the progress bar rectangle

    while pygame.mixer.music.get_busy():  # Loop while the song is playing
        current_time = pygame.mixer.music.get_pos() / 1000  # Get current song position in seconds
        progress = (current_time / total_length) * progress_width
        progress_canvas.delete("progress")  # Clear previous progress
        progress_canvas.create_rectangle(0, 0, progress, progress_height, fill="green", tags="progress")  # Draw the progress
        time.sleep(0.1)  # Sleep for 100ms to update progress smoothly


# Load the first song
def load_song():
    global current_song_index, song_path, total_length, total_length_str
    song_path = playlist[current_song_index]
    total_length = pygame.mixer.Sound(song_path).get_length()
    total_minutes, total_seconds = divmod(total_length, 60)  # Convert total length to minutes and seconds
    total_length_str = f"{int(total_minutes):02}:{int(total_seconds):02}"
    

load_song()


#this function is used to update time in the UI
def update_timer():
    if pygame.mixer.music.get_busy():
        # Get the current position of the song
        current_time = pygame.mixer.music.get_pos() / 1000  # Convert milliseconds to seconds
        minutes, seconds = divmod(current_time, 60)  # Convert seconds to minutes and seconds
        current_time_str = f"{int(minutes):02}:{int(seconds):02}"  # Format current time


        # Update the time_label with the current time and total length
        time_label.config(text=f"{current_time_str}                                                           {total_length_str}")


        # Call this function again after 1000 ms (1 second)
        root.after(1000, update_timer)


#function for pausing and unpausing
def toggle_music():
    if my_button["text"] == u"\u23F5":  # Play button pressed
        my_button["text"] = u"\u23F8"  # Change to pause icon
        if not pygame.mixer.music.get_busy():  # Only load and start song if not playing
            pygame.mixer.music.load(song_path)  # Load the song
            pygame.mixer.music.play()  # Start playback
            threading.Thread(target=update_progress, daemon=True).start()# time wala bar
            threading.Thread(target=update_visualizer, args=(song_path,), daemon=True).start()# hariyo haline wala
            update_timer()#time
        else:
            pygame.mixer.music.unpause()  # Resume if already playing and paused
    else:  # Pause button pressed
        my_button["text"] = u"\u23F5"  # Change to play icon
        pygame.mixer.music.pause()  # Pause the song

    

# Function to stop the music
def stop_music():
    pygame.mixer.music.stop()
    my_button["text"] = u"\u23F5"
    my_button["command"] = toggle_music


# Function to adjust the volume
def set_volume(val):
    volume = float(val) / 100  # Convert scale value to a float between 0.0 and 1.0
    pygame.mixer.music.set_volume(volume)


# Function to play the next song
def next_song():
    global current_song_index
    current_song_index = (current_song_index + 1) % len(playlist)
    load_song()
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play(loops=0)
    threading.Thread(target=update_progress, daemon=True).start() 
    threading.Thread(target=update_visualizer, args=(song_path,), daemon=True).start()  # Start visualizer
    update_timer()
    my_button["text"] = u"\u23F8"
    my_button["command"] = stop_music


# Function to play the previous song
def previous_song():
    global current_song_index
    current_song_index = (current_song_index - 1) % len(playlist)
    load_song()
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play(loops=0)
    threading.Thread(target=update_visualizer, args=(song_path,), daemon=True).start()  # Start visualizer
    threading.Thread(target=update_progress, daemon=True).start() 
    update_timer()
    my_button["text"] = u"\u23F8"
    my_button["command"] = stop_music


def draw_bars(bass_intensity):
    #Draw visualizer bars based on bass intensity.
    screen.fill(BLACK)
    num_bars = 50
    bar_width = WIDTH / num_bars

    for i in range(num_bars):
        # Add randomness to bar height for dynamic flickering
        height = bass_intensity * np.random.uniform(0.5, 1.5) * HEIGHT / 2  
        pygame.draw.rect(screen, BAR_COLOR,(i * bar_width, HEIGHT - height, bar_width - 2, height))
        pygame.display.flip()



# Update the visualizer using audio data
def fft_bass(data):
    #Perform FFT to extract bass frequencies and return intensity.
    fft_result = np.fft.fft(data)
    bass = np.abs(fft_result[:len(fft_result) // 4])  # Focus on lower frequencies (bass)
    bass_intensity = np.mean(bass) / 1000  # Normalize intensity to avoid overflow
    return min(bass_intensity, 1)  # Clamp the value to max 1 for better control


def update_visualizer(song_path):
    #Continuously update visualizer with bass data
    audio = AudioSegment.from_mp3(song_path)
    raw_data = np.array(audio.get_array_of_samples())
    num_channels = audio.channels
    chunk_size = 1024 * num_channels
    clock = pygame.time.Clock()

    # Loop over audio data in chunks
    for i in range(0, len(raw_data), chunk_size):
        chunk = raw_data[i:i + chunk_size]

        # Only update visualizer if music is playing
        if pygame.mixer.music.get_busy():
            bass_intensity = fft_bass(chunk)
            draw_bars(bass_intensity)
        else:
            screen.fill(BLACK)  # Clear visualizer if music stops
            pygame.display.flip()
            break  # Exit the loop

        # Handle Pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        clock.tick(30)  # Control visualizer update rate


#for making the background screen
background_screen = Listbox(root, bg="black", fg="green", width=700, height=80)
background_screen.pack(pady=0)


#for making the player widget
widget = Listbox(root, bg="grey", fg="green",width= 300, height=7 )
widget.place(x=0, y=603)


# Create a volume scale
volume_scale = Scale(root, from_=0, to=100, orient=HORIZONTAL, command=set_volume, bg="orange", fg="white")
volume_scale.set(100)  # Set initial volume to maximum
volume_scale.place(x=1125, y=623)


#creating a time label
time_label = Label(root, text="00:00                                                           00:00", font=("Helvetica", 11), bg="black", fg="grey")
time_label.place(x=489, y=568)


# Progress bar
progress_width = 200
progress_height = 15
progress_canvas = tk.Canvas(root, width=progress_width, height=progress_height, bg="grey", highlightthickness=0)
progress_canvas.place(x=548, y=573)


# Create the toggle button
my_button = Button(root, text=u"\u23F5", font=("Helvetica", 24), command=toggle_music,bg= "white" )
my_button.place(x=615, y=615)

# Create next and previous buttons
next_button = Button(root, text=u"\u23ED", font=("Helvetica", 24), command=next_song, bg="white")
next_button.place(x=690, y=615)


previous_button = Button(root, text=u"\u23EE", font=("Helvetica", 24), command=previous_song, bg="white")
previous_button.place(x=545, y=615)


#Options bar
menubar=Menu(root)
root.config(menu=menubar)



organize_menu = Menu(menubar,tearoff=False)
organize_menu.add_command(label = 'Pause/Play', command = toggle_music)
organize_menu.add_command(label = 'Next Song', command = next_song)
organize_menu.add_command(label = 'Previous Song', command = previous_song)


menubar.add_cascade(label ='Options',menu = organize_menu)


# Run the main event loop
root.mainloop()