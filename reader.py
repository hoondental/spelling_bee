import sys
import os
import time
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QLineEdit
)
from PyQt5.QtCore import QThread, pyqtSignal
from gtts import gTTS
import pygame
import uuid  # Add this import
import datetime

class WordReaderThread(QThread):
    update_word = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, words, interval=5):
        super().__init__()
        self.words = [words] if isinstance(words, str) else words 
        self.interval = interval
        self._is_running = True
        pygame.mixer.init()  # Initialize sound system

    

    def run(self):
        for word in self.words:
            if not self._is_running:
                break
            self.update_word.emit(word)
            try:
                filename = f"temp_{uuid.uuid4().hex}.mp3"  # Unique temp file
                tts = gTTS(text=word, lang='en')
                tts.save(filename)

                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                    
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                #pygame.mixer.quit()

                time.sleep(self.interval)

                # Clean up temp file
                if os.path.exists(filename):
                    os.remove(filename)

            except Exception as e:
                print(f"Error: {e}")
        self.finished.emit()


    def stop(self):
        self._is_running = False
        pygame.mixer.music.stop()




class SpellingBeeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spelling Bee Reader")
        self.resize(300, 200)

        self.layout = QVBoxLayout()

        self.label = QLabel("Load a word list to begin.")
        self.layout.addWidget(self.label)

        self.load_button = QPushButton("Load Word File")
        self.load_button.clicked.connect(self.load_words)
        self.layout.addWidget(self.load_button)

        self.start_button = QPushButton("Start Reading All")
        self.start_button.clicked.connect(self.start_reading)
        self.start_button.setEnabled(False)
        self.layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop All")
        self.stop_button.clicked.connect(self.stop_reading)
        self.stop_button.setEnabled(False)
        self.layout.addWidget(self.stop_button)
        
        self.start_test_button = QPushButton("Start Test")
        self.start_test_button.clicked.connect(self.start_test)
        self.start_test_button.setEnabled(False)
        self.layout.addWidget(self.start_test_button)
        
        self.end_test_button = QPushButton("End Test")
        self.end_test_button.clicked.connect(self.end_test)
        self.end_test_button.setEnabled(False)
        self.layout.addWidget(self.end_test_button)
        
        self.read_next_button = QPushButton("Read Next")
        self.read_next_button.clicked.connect(self.read_next)
        self.read_next_button.setEnabled(False)
        self.layout.addWidget(self.read_next_button)
        
        self.show_spelling_button = QPushButton("Show Spelling")
        self.show_spelling_button.clicked.connect(self.show_spelling)
        self.show_spelling_button.setEnabled(False)
        self.layout.addWidget(self.show_spelling_button)
        
        self.mark_incorrect_button = QPushButton("Mark Incorrect")
        self.mark_incorrect_button.clicked.connect(self.mark_incorrect)
        self.mark_incorrect_button.setEnabled(False)
        self.layout.addWidget(self.mark_incorrect_button)
        
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type spelling here and press Enter")
        self.input_box.returnPressed.connect(self.check_spelling)  # connect Enter press
        self.layout.addWidget(self.input_box)

        self.setLayout(self.layout)
        self.words = []
        self.incorrects = []
        self.reader_thread = None
        
        self.current_idx = -1

    def load_words(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Word List", "", "Text Files (*.txt)")
        if file_path:
            with open(file_path, "r") as f:
                self.words = [line.strip() for line in f if line.strip()]
            self.label.setText("Loaded {} words.".format(len(self.words)))
            self.start_button.setEnabled(True)
            self.read_next_button.setEnabled(True)
            self.start_test_button.setEnabled(True)

    def start_reading(self):
        if not self.words:
            return
        self.reader_thread = WordReaderThread(self.words, interval=5)
        self.reader_thread.update_word.connect(self.display_word)
        self.reader_thread.finished.connect(self.reading_finished)
        self.reader_thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_reading(self):
        if self.reader_thread:
            self.reader_thread.stop()
        self.stop_button.setEnabled(False)

    def display_word(self, word):
        self.label.setText(f"Reading: {word}")

    def reading_finished(self):
        self.label.setText("Done reading.")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        if os.path.exists("temp.mp3"):
            os.remove("temp.mp3")
            
    def start_test(self):
        if not self.words:
            return
        self.current_idx = -1
        self.incorrects = []
        self.start_test_button.setEnabled(False)
        self.end_test_button.setEnabled(True)    
        self.read_next()
        
    def end_test(self):
        self.end_test_button.setEnabled(False)
        self.start_test_button.setEnabled(True)
        filename = f"incorrects_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        with open(filename, "w") as f:
            f.write("\n".join(': '.join(item) for item in self.incorrects))
        
        
    def read_next(self):
        self.current_idx = (self.current_idx + 1) % len(self.words)
        word = self.words[self.current_idx]
        self.input_box.setText("")
        self.reader_thread = WordReaderThread(word, interval=1)
        self.reader_thread.start()        
        self.show_spelling_button.setEnabled(True)
        self.mark_incorrect_button.setEnabled(True)
        
        if self.current_idx == len(self.words) - 1:
            self.read_next_button.setEnabled(False)
            self.end_test()
        
    def show_spelling(self):
        word = self.words[self.current_idx]
        self.label.setText(f"Spelling: {word}")
        
    def mark_incorrect(self):
        self.record_incorrect()
        self.mark_incorrect_button.setEnabled(False)
        
    def record_incorrect(self, input_text=''):
        word = self.words[self.current_idx]
        self.incorrects.append((word, input_text))
        self.label.setText(f"Incorrect: {word}")
        self.mark_incorrect_button.setEnabled(False)
        
    def check_spelling(self):
        word = self.words[self.current_idx]
        input_text = self.input_box.text().strip()
        if word == self.input_box.text().strip():
            self.label.setText(f"Correct: {word}")
        else:
            self.label.setText(f"Incorrect: {word}")
            self.record_incorrect(input_text=input_text)
        self.read_next()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpellingBeeApp()
    window.show()
    sys.exit(app.exec_())