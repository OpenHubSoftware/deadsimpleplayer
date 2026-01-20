import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QPushButton, QLabel, QSlider, 
                              QTreeView, QListWidget, QListWidgetItem, QSplitter)
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, Qt, QDir
from PyQt6.QtGui import QFileSystemModel, QKeyEvent, QFont

class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dead Simple Music Player")
        self.setGeometry(100, 100, 950, 650)
        
        # Audio formats we support
        self.audio_extensions = ['.mp3', '.flac', '.wav', '.m4a', '.ogg', 
                                '.wma', '.aac', '.alac', '.opus']
        
        # Track current song index
        self.current_index = -1
        
        # Track if user is dragging the slider
        self.slider_being_dragged = False
        
        # Initialize audio player
        self.audio_output = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.audio_output)
        
        # Connect signals for progress and auto-advance
        self.player.positionChanged.connect(self.update_position)
        self.player.durationChanged.connect(self.update_duration)
        self.player.mediaStatusChanged.connect(self.on_media_status_changed)
        
        # Setup UI
        self.setup_ui()
        
        # Apply stylesheet
        self.apply_stylesheet()
        
    def setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create splitter for folder tree and file list
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # LEFT SIDE - Folder Tree
        self.folder_tree = QTreeView()
        self.folder_model = QFileSystemModel()
        self.folder_model.setRootPath('')
        self.folder_model.setFilter(QDir.Filter.AllDirs | QDir.Filter.NoDotAndDotDot)
        self.folder_tree.setModel(self.folder_model)
        
        # Hide extra columns
        self.folder_tree.setColumnHidden(1, True)
        self.folder_tree.setColumnHidden(2, True)
        self.folder_tree.setColumnHidden(3, True)
        
        # Set starting folder to user's Music folder
        music_path = str(Path.home() / "Music")
        if os.path.exists(music_path):
            self.folder_tree.setRootIndex(self.folder_model.index(music_path))
        else:
            self.folder_tree.setRootIndex(self.folder_model.index(str(Path.home())))
        
        self.folder_tree.clicked.connect(self.folder_selected)
        
        # RIGHT SIDE - File List
        self.file_list = QListWidget()
        self.file_list.itemDoubleClicked.connect(self.play_selected_file)
        
        # Add both to splitter
        splitter.addWidget(self.folder_tree)
        splitter.addWidget(self.file_list)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        main_layout.addWidget(splitter)
        
        # Song info label
        self.song_label = QLabel("No song loaded")
        self.song_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.song_label.setObjectName("songLabel")
        font = QFont("JetBrains Mono", 11, QFont.Weight.Bold)
        self.song_label.setFont(font)
        main_layout.addWidget(self.song_label)
        
        # Progress bar
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(8)
        
        self.time_label = QLabel("0:00")
        self.time_label.setObjectName("timeLabel")
        progress_layout.addWidget(self.time_label)
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 0)
        self.progress_slider.sliderMoved.connect(self.set_position)
        self.progress_slider.sliderPressed.connect(self.slider_pressed)
        self.progress_slider.sliderReleased.connect(self.slider_released)
        self.progress_slider.setObjectName("progressSlider")
        progress_layout.addWidget(self.progress_slider)
        
        self.duration_label = QLabel("0:00")
        self.duration_label.setObjectName("timeLabel")
        progress_layout.addWidget(self.duration_label)
        
        main_layout.addLayout(progress_layout)
        
        # Control buttons layout
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # Previous button
        self.prev_btn = QPushButton("⏮ PREV")
        self.prev_btn.clicked.connect(self.play_previous)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setObjectName("controlButton")
        button_layout.addWidget(self.prev_btn)
        
        # Play button
        self.play_btn = QPushButton("▶ PLAY")
        self.play_btn.clicked.connect(self.play_pause)
        self.play_btn.setEnabled(False)
        self.play_btn.setObjectName("playButton")
        button_layout.addWidget(self.play_btn)
        
        # Stop button
        self.stop_btn = QPushButton("■ STOP")
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setObjectName("controlButton")
        button_layout.addWidget(self.stop_btn)
        
        # Next button
        self.next_btn = QPushButton("NEXT ⏭")
        self.next_btn.clicked.connect(self.play_next)
        self.next_btn.setEnabled(False)
        self.next_btn.setObjectName("controlButton")
        button_layout.addWidget(self.next_btn)
        
        main_layout.addLayout(button_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(8)
        
        volume_label = QLabel("🔊 VOLUME")
        volume_label.setObjectName("volumeLabel")
        volume_layout.addWidget(volume_label)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMinimum(0)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.volume_slider.setObjectName("volumeSlider")
        volume_layout.addWidget(self.volume_slider)
        
        self.volume_label = QLabel("70%")
        self.volume_label.setObjectName("volumePercent")
        volume_layout.addWidget(self.volume_label)
        
        main_layout.addLayout(volume_layout)
        
        # Keyboard shortcut hint
        hint_label = QLabel("⌨ SPACEBAR: Play/Pause  |  ← → : Prev/Next")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setObjectName("hintLabel")
        main_layout.addWidget(hint_label)
        
        # Set initial volume
        self.audio_output.setVolume(0.7)
        
    def apply_stylesheet(self):
        stylesheet = """
        /* Main Window - Matches Dead Simple Website */
        QMainWindow {
            background-color: #0d0d0d;
        }
        
        /* Central Widget */
        QWidget {
            background-color: #0d0d0d;
            color: #e0e0e0;
            font-family: 'JetBrains Mono', 'Consolas', 'Courier New', monospace;
        }
        
        /* Folder Tree */
        QTreeView {
            background-color: #1a1a1a;
            border: 1px solid #1a1a1a;
            border-radius: 0px;
            padding: 5px;
            color: #e0e0e0;
            selection-background-color: #00f3ff;
        }
        
        QTreeView::item:hover {
            background-color: rgba(0, 243, 255, 0.1);
        }
        
        QTreeView::item:selected {
            background-color: #00f3ff;
            color: #0d0d0d;
            font-weight: bold;
        }
        
        /* File List */
        QListWidget {
            background-color: #1a1a1a;
            border: 1px solid #1a1a1a;
            border-radius: 0px;
            padding: 5px;
            color: #e0e0e0;
            font-size: 10pt;
        }
        
        QListWidget::item {
            padding: 8px;
            border-radius: 0px;
        }
        
        QListWidget::item:hover {
            background-color: rgba(0, 243, 255, 0.1);
        }
        
        QListWidget::item:selected {
            background-color: #00f3ff;
            color: #0d0d0d;
            font-weight: bold;
        }
        
        /* Song Label */
        #songLabel {
            background: rgba(0, 243, 255, 0.05);
            border: 1px solid #00f3ff;
            border-radius: 0px;
            padding: 12px;
            color: #00f3ff;
            min-height: 25px;
        }
        
        /* Time Labels */
        #timeLabel {
            color: #00f3ff;
            font-weight: bold;
            font-size: 11pt;
            min-width: 45px;
        }
        
        /* Progress Slider */
        #progressSlider {
            height: 20px;
        }
        
        #progressSlider::groove:horizontal {
            border: 1px solid #1a1a1a;
            height: 8px;
            background: #1a1a1a;
            border-radius: 0px;
        }
        
        #progressSlider::handle:horizontal {
            background: #00f3ff;
            border: none;
            width: 16px;
            margin: -5px 0;
            border-radius: 0px;
        }
        
        #progressSlider::handle:horizontal:hover {
            background: #00ffff;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
        }
        
        #progressSlider::sub-page:horizontal {
            background: rgba(0, 243, 255, 0.3);
            border-radius: 0px;
        }
        
        /* Control Buttons */
        #controlButton {
            background: transparent;
            border: 1px solid #555;
            border-radius: 0px;
            padding: 12px 20px;
            color: #e0e0e0;
            font-weight: bold;
            font-size: 11pt;
            min-width: 100px;
        }
        
        #controlButton:hover:enabled {
            border: 1px solid #00f3ff;
            color: #00f3ff;
            background: rgba(0, 243, 255, 0.05);
        }
        
        #controlButton:pressed:enabled {
            background: rgba(0, 243, 255, 0.1);
            border: 1px solid #00f3ff;
        }
        
        #controlButton:disabled {
            background: transparent;
            border: 1px solid #333;
            color: #555;
        }
        
        /* Play Button - Special Styling */
        #playButton {
            background: transparent;
            border: 1px solid #00f3ff;
            border-radius: 0px;
            padding: 12px 20px;
            color: #00f3ff;
            font-weight: bold;
            font-size: 11pt;
            min-width: 100px;
        }
        
        #playButton:hover:enabled {
            background: #00f3ff;
            color: #0d0d0d;
            box-shadow: 0 0 20px rgba(0, 243, 255, 0.5);
        }
        
        #playButton:pressed:enabled {
            background: #00d4ff;
            color: #0d0d0d;
        }
        
        #playButton:disabled {
            background: transparent;
            border: 1px solid #333;
            color: #555;
        }
        
        /* Volume Label */
        #volumeLabel {
            color: #00f3ff;
            font-weight: bold;
            font-size: 10pt;
        }
        
        #volumePercent {
            color: #00f3ff;
            font-weight: bold;
            font-size: 11pt;
            min-width: 45px;
        }
        
        /* Volume Slider */
        #volumeSlider {
            height: 20px;
        }
        
        #volumeSlider::groove:horizontal {
            border: 1px solid #1a1a1a;
            height: 8px;
            background: #1a1a1a;
            border-radius: 0px;
        }
        
        #volumeSlider::handle:horizontal {
            background: #00f3ff;
            border: none;
            width: 16px;
            margin: -5px 0;
            border-radius: 0px;
        }
        
        #volumeSlider::handle:horizontal:hover {
            background: #00ffff;
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.5);
        }
        
        #volumeSlider::sub-page:horizontal {
            background: rgba(0, 243, 255, 0.3);
            border-radius: 0px;
        }
        
        /* Hint Label */
        #hintLabel {
            color: #555;
            font-size: 9pt;
            padding: 5px;
        }
        
        /* Scrollbars */
        QScrollBar:vertical {
            border: none;
            background: #1a1a1a;
            width: 12px;
        }
        
        QScrollBar::handle:vertical {
            background: #333;
            min-height: 20px;
        }
        
        QScrollBar::handle:vertical:hover {
            background: #00f3ff;
        }
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        QScrollBar:horizontal {
            border: none;
            background: #1a1a1a;
            height: 12px;
        }
        
        QScrollBar::handle:horizontal {
            background: #333;
            min-width: 20px;
        }
        
        QScrollBar::handle:horizontal:hover {
            background: #00f3ff;
        }
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }
        """
        
        self.setStyleSheet(stylesheet)
        
    def folder_selected(self, index):
        # Get the selected folder path
        folder_path = self.folder_model.filePath(index)
        
        # Clear current file list
        self.file_list.clear()
        self.current_index = -1
        
        # Get all audio files in this folder
        try:
            files = os.listdir(folder_path)
            audio_files = []
            
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in self.audio_extensions:
                    audio_files.append(file)
            
            # Sort files alphabetically
            audio_files.sort()
            
            # Add to list
            for audio_file in audio_files:
                item = QListWidgetItem(audio_file)
                item.setData(Qt.ItemDataRole.UserRole, os.path.join(folder_path, audio_file))
                self.file_list.addItem(item)
                
        except PermissionError:
            self.song_label.setText("⚠ Permission denied for this folder")
        except Exception as e:
            self.song_label.setText(f"⚠ Error reading folder: {str(e)}")
    
    def play_selected_file(self, item):
        # Find the index of the clicked item
        self.current_index = self.file_list.row(item)
        self.play_current_song()
    
    def play_current_song(self):
        if self.current_index < 0 or self.current_index >= self.file_list.count():
            return
        
        # Get current item
        item = self.file_list.item(self.current_index)
        file_path = item.data(Qt.ItemDataRole.UserRole)
        
        # Highlight current song
        self.file_list.setCurrentRow(self.current_index)
        
        # Load and play the audio file
        self.player.setSource(QUrl.fromLocalFile(file_path))
        self.player.play()
        
        # Update UI
        filename = os.path.basename(file_path)
        self.song_label.setText(f"♪ NOW PLAYING: {filename}")
        self.play_btn.setText("⏸ PAUSE")
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(True)
        
        # Enable prev/next buttons
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < self.file_list.count() - 1)
    
    def play_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.play_current_song()
    
    def play_next(self):
        if self.current_index < self.file_list.count() - 1:
            self.current_index += 1
            self.play_current_song()
    
    def on_media_status_changed(self, status):
        # Auto-advance to next song when current one finishes
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            if self.current_index < self.file_list.count() - 1:
                self.play_next()
            else:
                # Reached end of playlist
                self.stop()
                self.song_label.setText("♪ PLAYLIST FINISHED")
            
    def play_pause(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.play_btn.setText("▶ PLAY")
        else:
            self.player.play()
            self.play_btn.setText("⏸ PAUSE")
            
    def stop(self):
        self.player.stop()
        self.play_btn.setText("▶ PLAY")
        
    def change_volume(self, value):
        volume = value / 100.0
        self.audio_output.setVolume(volume)
        self.volume_label.setText(f"{value}%")
    
    def update_position(self, position):
        # Only update slider if user is not dragging it
        if not self.slider_being_dragged:
            self.progress_slider.setValue(position)
        self.time_label.setText(self.format_time(position))
    
    def slider_pressed(self):
        self.slider_being_dragged = True
    
    def slider_released(self):
        self.slider_being_dragged = False
        self.set_position(self.progress_slider.value())
    
    def update_duration(self, duration):
        self.progress_slider.setRange(0, duration)
        self.duration_label.setText(self.format_time(duration))
    
    def set_position(self, position):
        self.player.setPosition(position)
    
    def format_time(self, ms):
        """Convert milliseconds to MM:SS format"""
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def keyPressEvent(self, event: QKeyEvent):
        """Handle keyboard shortcuts"""
        if event.key() == Qt.Key.Key_Space:
            if self.play_btn.isEnabled():
                self.play_pause()
        elif event.key() == Qt.Key.Key_Left:
            if self.prev_btn.isEnabled():
                self.play_previous()
        elif event.key() == Qt.Key.Key_Right:
            if self.next_btn.isEnabled():
                self.play_next()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = MusicPlayer()
    player.show()
    sys.exit(app.exec())
