import sys
import os
import vlc
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QSlider, QLabel, QSizePolicy, QShortcut
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence

#Directory path for VLC libraries
os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')

class ClickableSlider(QSlider):
    """
    Custom QSlider implementation.
    Allows the user to jump to a specific point in the video just by clicking anywhere on the track,
    instead of having to drag the handle manually.
    """
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # Calculate the new slider value based on the exact pixel coordinates of the mouse click
            val = self.minimum() + ((self.maximum() - self.minimum()) * event.x()) / self.width()
            self.setValue(int(val))
            self.sliderMoved.emit(int(val))
        super().mousePressEvent(event)
        
class MediaPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multimedia Player")
        self.setGeometry(100, 100, 800, 600)
        
        # Set the main window background and style the buttons for a modern Dark Mode UI
        self.setStyleSheet("""
            QMainWindow {
                background-color: black;
            }
            QPushButton {
                background-color: #3b3b3b;
                color: white;
                border: 1px solid #555555;
                padding: 7px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #007ACC;
                border: 1px solid #00A6FF;
            }
            QPushButton:pressed {
                background-color: #005A99;
            }
        """)

        #SET UP THE VLC ENGINE
        # Initialize the underlying VLC instance and create a media player object
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        #CREATE THE MAIN INTERFACE
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        # Remove margins so the video frame reaches the window edges perfectly
        self.layout.setContentsMargins(0, 0, 0, 0) 
        self.central_widget.setLayout(self.layout)

        #THE VIDEO SCREEN
        self.video_frame = QWidget(self)
        self.video_frame.setStyleSheet("background-color: black;")
        # Tell the video frame to expand as much as possible, pushing controls to the bottom
        self.video_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.layout.addWidget(self.video_frame)

        #TIME SLIDER
        self.position_slider = ClickableSlider(Qt.Horizontal, self)
        self.position_slider.setMaximum(1000)
        self.position_slider.setStyleSheet("margin-left: 10px; margin-right: 10px;")
        
        # Connect slider events to our custom functions
        self.position_slider.sliderMoved.connect(self.set_position)
        self.position_slider.sliderPressed.connect(self.start_dragging)
        self.position_slider.sliderReleased.connect(self.stop_dragging)
        
        self.layout.addWidget(self.position_slider)
        self.is_dragging = False # Flag to prevent UI updates while the user is seeking
        
        #CONTROL BAR
        self.control_container = QWidget()
        self.control_container.setStyleSheet("background-color: #2b2b2b;") 
        self.control_layout = QHBoxLayout(self.control_container)
        self.control_layout.setContentsMargins(10, 5, 10, 10)
        self.layout.addWidget(self.control_container)

        # BUTTONS 
        # setFocusPolicy(Qt.NoFocus) prevents the Spacebar from accidentally clicking the last used button
        
        self.btn_open = QPushButton("Open Video")
        self.btn_open.setFocusPolicy(Qt.NoFocus) 
        self.btn_open.clicked.connect(self.open_file)
        self.control_layout.addWidget(self.btn_open)

        self.btn_play = QPushButton("Play / Pause")
        self.btn_play.setFocusPolicy(Qt.NoFocus)
        self.btn_play.clicked.connect(self.play_pause)
        self.control_layout.addWidget(self.btn_play)

        self.btn_fullscreen = QPushButton("Full-Screen")
        self.btn_fullscreen.setFocusPolicy(Qt.NoFocus)
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        self.control_layout.addWidget(self.btn_fullscreen)

        self.btn_subs = QPushButton("Load Subtitles (.srt)")
        self.btn_subs.setFocusPolicy(Qt.NoFocus)
        self.btn_subs.clicked.connect(self.load_subtitles)
        self.control_layout.addWidget(self.btn_subs)
        
        # VOLUME CONTROLS 
        self.control_layout.addStretch(1) # Pushes the volume slider to the far right
        
        self.volume_container = QWidget()
        self.volume_hbox = QHBoxLayout(self.volume_container)
        self.volume_hbox.setContentsMargins(0, 0, 0, 0) 
        
        self.volume_label = QLabel("Volume:")
        self.volume_label.setStyleSheet("color: white;") 
        self.volume_hbox.addWidget(self.volume_label)
        
        self.volume_slider = QSlider(Qt.Horizontal, self)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(100) 
        self.volume_slider.setFixedWidth(120)
        self.volume_slider.setFocusPolicy(Qt.NoFocus)
        self.volume_slider.valueChanged.connect(self.set_volume)
        self.volume_hbox.addWidget(self.volume_slider)

        self.control_layout.addWidget(self.volume_container)
        self.is_fullscreen = False
        
        # TIMER 
        # A timer that queries the VLC player every 100ms to update the timeline slider
        self.timer = QTimer(self)
        self.timer.setInterval(100) 
        self.timer.timeout.connect(self.update_ui)

        # KEYBOARD SHORTCUTS 
        self.shortcut_space = QShortcut(QKeySequence("Space"), self)
        self.shortcut_space.activated.connect(self.play_pause)

        self.shortcut_esc = QShortcut(QKeySequence("Esc"), self)
        self.shortcut_esc.activated.connect(self.exit_fullscreen)

    # LOGIC AND ACTIONS 

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Choose Video", ".", "Video Files (*.mp4 *.avi *.mkv)")
        if filename: 
            media = self.instance.media_new(filename)
            self.media_player.set_media(media)

            # BINDING THE VIDEO OUTPUT:
            # VLC requires a native OS window handle to render hardware-accelerated video.
            # Map the PyQt widget ID to the correct VLC function based on the platform.
            if sys.platform.startswith('linux'): # Linux (X11)
                self.media_player.set_xwindow(self.video_frame.winId())
            elif sys.platform == "win32":        # Windows
                self.media_player.set_hwnd(self.video_frame.winId())
            elif sys.platform == "darwin":       # macOS
                self.media_player.set_nsobject(int(self.video_frame.winId()))
            
            self.media_player.play()
            self.timer.start()

    def play_pause(self):
        # If the video has reached the end, hitting play restarts it from the beginning
        
        if self.media_player.get_state() == vlc.State.Ended:
            self.media_player.stop()
            self.media_player.play()
            self.position_slider.setValue(0)
            self.timer.start()
        elif self.media_player.is_playing():
            self.media_player.pause()
        else:
            self.media_player.play()

    def toggle_fullscreen(self):
        if not self.is_fullscreen:
            self.showFullScreen() 
            self.is_fullscreen = True
        else:
            self.showNormal() 
            self.is_fullscreen = False

    def exit_fullscreen(self):
        # Dedicated function to escape fullscreen via the ESC key
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False

    def load_subtitles(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Choose Subtitles", ".", "Subtitles (*.srt)")
        if filename:
            # Normalize path for Windows compatibility
            filename = os.path.normpath(filename)
            self.media_player.video_set_subtitle_file(filename)
            
            # Force VLC to display the subtitle track immediately (Track 1)
            self.media_player.video_set_spu(1)

    def set_volume(self, volume):
        self.media_player.audio_set_volume(volume)
    
    def start_dragging(self):
        self.is_dragging = True

    def stop_dragging(self):
        self.is_dragging = False
        val = self.position_slider.value()
        
        # If the video ended, we must restart it first.
        # VLC needs a fraction of a second to reopen the file stream before it can seek.
        if self.media_player.get_state() == vlc.State.Ended:
            self.media_player.stop()
            self.media_player.play()
            self.timer.start()
            # Wait 100ms, then apply the new position
            QTimer.singleShot(100, lambda: self.media_player.set_position(val / 1000.0))
        else:
            self.media_player.set_position(val / 1000.0)

    def set_position(self, position):
        # Live update of the video position while dragging the slider
        if self.media_player.get_state() != vlc.State.Ended:
            vlc_position = position / 1000.0
            self.media_player.set_position(vlc_position)

    def update_ui(self):
        # Do not interfere with the slider if the user is currently holding it
        if self.is_dragging:
            return
            
        state = self.media_player.get_state()
        
        # When video ends, snap the slider to 100% and stop the polling timer
        if state == vlc.State.Ended:
            self.position_slider.setValue(1000)
            self.timer.stop()
            return
            
        # Normal playback update
        if state == vlc.State.Playing:
            current_pos = int(self.media_player.get_position() * 1000)
            # Ignore negative values sometimes outputted by VLC during transitions
            if current_pos >= 0:
                self.position_slider.setValue(current_pos)
        
# APPLICATION STARTUP 
if __name__ == "__main__":
    
    app = QApplication(sys.argv) 
    app.setStyle("Fusion")       
    player = MediaPlayer()       
    player.show()                
    sys.exit(app.exec_())