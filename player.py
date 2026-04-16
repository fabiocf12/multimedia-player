import sys
import os
import vlc
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog


class MediaPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multimedia Player")
        self.setGeometry(100, 100, 800, 600) # x, y, width, height

        # 1. SET UP THE VLC ENGINE
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        # 2. CREATE THE MAIN INTERFACE (The Window)
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout() # Vertical layout (stacks things top to bottom)
        self.central_widget.setLayout(self.layout)

        # 3. THE VIDEO SCREEN
        # This is the black rectangle where the video will be rendered.
        self.video_frame = QWidget(self)
        self.video_frame.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.video_frame)

        # 4. THE CONTROL BAR (Buttons at the bottom)
        self.control_layout = QHBoxLayout() # Horizontal layout (side-by-side)
        self.layout.addLayout(self.control_layout)

        # --- BUTTONS ---
        # Create button -> Tell it what function to run when clicked -> Add to layout
        self.btn_open = QPushButton("Open Video")
        self.btn_open.clicked.connect(self.open_file)
        self.control_layout.addWidget(self.btn_open)

        self.btn_play = QPushButton("Play / Pause")
        self.btn_play.clicked.connect(self.play_pause)
        self.control_layout.addWidget(self.btn_play)

        self.btn_fullscreen = QPushButton("Full-Screen")
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        self.control_layout.addWidget(self.btn_fullscreen)

        self.btn_subs = QPushButton("Toggle Subtitles")
        self.btn_subs.clicked.connect(self.toggle_subtitles)
        self.control_layout.addWidget(self.btn_subs)

        self.is_fullscreen = False

    # --- LOGIC / ACTIONS ---

    def open_file(self):
        # Opens a native file dialog to choose the media file
        filename, _ = QFileDialog.getOpenFileName(self, "Choose Video", ".", "Video Files (*.mp4 *.avi *.mkv)")
        
        if filename: # If the user actually selected a file (didn't click cancel)
            # Load the file into the VLC engine
            media = self.instance.media_new(filename)
            self.media_player.set_media(media)

            # THE MAGIC LINK: Connecting VLC's video output to our PyQt black rectangle
            # We need to get the unique window ID based on the Operating System
            if sys.platform.startswith('linux'): # Linux
                self.media_player.set_xwindow(self.video_frame.winId())
            elif sys.platform == "win32":        # Windows
                self.media_player.set_hwnd(self.video_frame.winId())
            elif sys.platform == "darwin":       # MacOS
                self.media_player.set_nsobject(int(self.video_frame.winId()))
            
            # Start playing! Audio works automatically.
            self.media_player.play()

    def play_pause(self):
        # Check if it's currently playing, and toggle accordingly
        if self.media_player.is_playing():
            self.media_player.pause()
        else:
            self.media_player.play()

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.showFullScreen() # PyQt function to maximize without borders
            self.is_fullscreen = True
        else:
            self.showNormal() # PyQt function to return to windowed mode
            self.is_fullscreen = False

    def toggle_subtitles(self):
        # VLC manages subtitle tracks by numbers. 0 = Off, 1 = Track 1, etc.
        current_spu = self.media_player.video_get_spu()
        if current_spu > 0:
            self.media_player.video_set_spu(0) # Turn Off
            print("Subtitles: OFF")
        else:
            self.media_player.video_set_spu(1) # Turn On (Track 1)
            print("Subtitles: ON")

# --- APPLICATION STARTUP ---
if __name__ == "__main__":
    app = QApplication(sys.argv) # Starts the PyQt event loop (keeps window open)
    app.setStyle("Fusion")       # Makes it look slightly more modern
    player = MediaPlayer()       # Creates an instance of our class
    player.show()                # Draws the window on the screen
    sys.exit(app.exec_())        # Safely closes Python when the window is closed