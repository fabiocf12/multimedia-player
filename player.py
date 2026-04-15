import sys
import vlc
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog

class MediaPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Multimedia Player")
        self.setGeometry(100, 100, 800, 600)

        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()

        # 2. Criar a Interface Principal
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Onde o vídeo vai ser desenhado (um retângulo preto)
        self.video_frame = QWidget(self)
        self.video_frame.setStyleSheet("background-color: black;")
        self.layout.addWidget(self.video_frame)

        # Barra de Controlos em baixo
        self.control_layout = QHBoxLayout()
        self.layout.addLayout(self.control_layout)

        # --- BOTÕES ---
        self.btn_open = QPushButton("Abrir Vídeo")
        self.btn_open.clicked.connect(self.open_file)
        self.control_layout.addWidget(self.btn_open)

        self.btn_play = QPushButton("Play / Pause")
        self.btn_play.clicked.connect(self.play_pause)
        self.control_layout.addWidget(self.btn_play)

        self.btn_fullscreen = QPushButton("Full-Screen")
        self.btn_fullscreen.clicked.connect(self.toggle_fullscreen)
        self.control_layout.addWidget(self.btn_fullscreen)

        self.btn_subs = QPushButton("Alternar Legendas")
        self.btn_subs.clicked.connect(self.toggle_subtitles)
        self.control_layout.addWidget(self.btn_subs)

        self.is_fullscreen = False

    # --- LÓGICA DAS AÇÕES ---

    def open_file(self):
        # Abre a janela para escolheres o ficheiro MP4, MKV, AVI, etc.
        filename, _ = QFileDialog.getOpenFileName(self, "Escolhe o vídeo", ".", "Video Files (*.mp4 *.avi *.mkv)")
        if filename:
            media = self.instance.media_new(filename)
            self.media_player.set_media(media)

            # A MAGIA: Ligar o vídeo do VLC à nossa janela do PyQt
            # Precisamos de verificar o sistema operativo porque cada um lida com janelas de forma diferente
            if sys.platform.startswith('linux'): # Linux (ex: se usares no Ubuntu)
                self.media_player.set_xwindow(self.video_frame.winId())
            elif sys.platform == "win32":        # Windows
                self.media_player.set_hwnd(self.video_frame.winId())
            elif sys.platform == "darwin":       # MacOS
                self.media_player.set_nsobject(int(self.video_frame.winId()))
            
            # Tocar o vídeo! O som vai sair automaticamente.
            self.media_player.play()

    def play_pause(self):
        if self.media_player.is_playing():
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

    def toggle_subtitles(self):
        # O VLC gere faixas de legendas. 0 = Desligado, 1 = Faixa 1, etc.
        # Se tiveres um ficheiro .srt com o mesmo nome do vídeo na mesma pasta, o VLC carrega-o logo na faixa 1.
        current_spu = self.media_player.video_get_spu()
        if current_spu > 0:
            self.media_player.video_set_spu(0) # Desliga
            print("Legendas: OFF")
        else:
            self.media_player.video_set_spu(1) # Liga a primeira faixa disponível
            print("Legendas: ON")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Dá um visual um pouco mais moderno aos botões
    player = MediaPlayer()
    player.show()
    sys.exit(app.exec_())