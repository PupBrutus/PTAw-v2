import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QDialog, QLineEdit, QFormLayout, QProgressBar, QHBoxLayout, QComboBox, QColorDialog, QMessageBox, QFileDialog 
from PyQt5.QtGui import QColor
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtMultimedia import QSound
import random

current_dir = os.path.dirname(os.path.realpath(__file__))
appdata = os.getenv('APPDATA')
global presets_file 
presets_file = os.path.join(appdata, 'PTAW', 'presets.json')


class Timer:
    def __init__(self, name, min_time, max_time, color, sound_effect):
        self.name = name
        self.min_time = min_time
        self.max_time = max_time
        self.color = color
        self.sound_effect = os.path.join(current_dir, sound_effect)

    def start(self):
        return random.uniform(self.min_time, self.max_time)
    
class SettingsWindow(QDialog):
    def __init__(self, parent=None, timers=None, presets=None, hit_count_min=None, hit_count_max=None):
        super(SettingsWindow, self).__init__(parent)
        self.timers = timers
        self.presets = presets
        self.hit_count_min = hit_count_min
        self.hit_count_max = hit_count_max
        self.last_preset = None

        # Initialize the sound paths with the current sound paths from the App instance
        self.prepare_sound_path = self.parent().prepare_sound_path
        self.hit_sound_path = self.parent().hit_sound_path
        self.hold_sound_path = self.parent().hold_sound_path
        self.release_sound_path = self.parent().release_sound_path

        self.initUI()
        self.update_settings_UI()

    def initUI(self):
        self.layout = QFormLayout(self)

        self.preset_dropdown = QComboBox(self)  # Create a new dropdown
        self.preset_dropdown.setEditable(True)  # Make the dropdown editable
        self.preset_dropdown.addItems(self.presets.keys())  # Add the names of the presets to the dropdown
        self.preset_dropdown.currentIndexChanged.connect(self.load_preset)  # Connect the dropdown to the load_preset method
        self.preset_dropdown.setCurrentText(self.last_preset)  # Set the current text to the last activated preset
        self.layout.addRow('Presets', self.preset_dropdown)  # Add the dropdown to the layout

        save_button = QPushButton('Save Preset', self)
        save_button.clicked.connect(self.save_preset)
        self.layout.addRow(save_button)

        delete_button = QPushButton('Delete Preset', self)
        delete_button.clicked.connect(self.delete_preset)
        self.layout.addRow(delete_button)

        # Create buttons for the sound files
        self.prepare_sound_button = QPushButton('Select Prepare Sound', self)
        self.hit_sound_button = QPushButton('Select Hit Sound', self)
        self.hold_sound_button = QPushButton('Select Hold Sound', self)
        self.release_sound_button = QPushButton('Select Release Sound', self)

        # Connect the buttons to methods that open the file dialogs
        self.prepare_sound_button.clicked.connect(self.select_prepare_sound)
        self.hit_sound_button.clicked.connect(self.select_hit_sound)
        self.hold_sound_button.clicked.connect(self.select_hold_sound)
        self.release_sound_button.clicked.connect(self.select_release_sound)



        self.inputs = []
        self.color_buttons = []  # List to store the color buttons
        for timer in self.timers:
            min_input = QLineEdit(str(timer.min_time))
            max_input = QLineEdit(str(timer.max_time))
            self.inputs.append((min_input, max_input))
            self.layout.addRow(f'{timer.name} min sec', min_input)
            self.layout.addRow(f'{timer.name} max sec', max_input)

            color_button = QPushButton('Select Color', self)  # Create a new button for selecting the color
            color_button.clicked.connect(lambda _, t=timer: self.select_color(t))  # Connect the button to the select_color method
            self.color_buttons.append(color_button)
            self.layout.addRow(f'{timer.name} color', color_button)  # Add the button to the layout

        self.hit_count_min_input = QLineEdit(str(self.hit_count_min))
        self.hit_count_max_input = QLineEdit(str(self.hit_count_max))
        self.layout.addRow('Hit count min', self.hit_count_min_input)
        self.layout.addRow('Hit count max', self.hit_count_max_input)

        # Add the buttons to the layout
        self.layout.addRow('Prepare Sound', self.prepare_sound_button)
        self.layout.addRow('Hit Sound', self.hit_sound_button)
        self.layout.addRow('Hold Sound', self.hold_sound_button)
        self.layout.addRow('Release Sound', self.release_sound_button)

        apply_button = QPushButton('Apply', self)
        apply_button.clicked.connect(self.apply)
        self.layout.addRow(apply_button)

    # Select Color
    def select_color(self, timer):
        color = QColorDialog.getColor()  # Open the color dialog and get the selected color
        if color.isValid():  # If a color was selected
            timer.color = color.name()  # Update the color of the timer
        self.update_settings_UI()  # Update the UI to reflect the new color

    # Select Prepare Sound
        
    def select_prepare_sound(self):
        self.prepare_sound_path = QFileDialog.getOpenFileName(self, 'Select Prepare Sound', '', 'Sound Files (*.wav)')[0]

    def select_hit_sound(self):
        self.hit_sound_path = QFileDialog.getOpenFileName(self, 'Select Hit Sound', '', 'Sound Files (*.wav)')[0]

    def select_hold_sound(self):
        self.hold_sound_path = QFileDialog.getOpenFileName(self, 'Select Hold Sound', '', 'Sound Files (*.wav)')[0]

    def select_release_sound(self):
        self.release_sound_path = QFileDialog.getOpenFileName(self, 'Select Release Sound', '', 'Sound Files (*.wav)')[0]

    # Apply Settings to current session
    def apply(self):
        for timer, (min_input, max_input) in zip(self.timers, self.inputs):
            timer.min_time = float(min_input.text())
            timer.max_time = float(max_input.text())
        self.hit_count_min = int(self.hit_count_min_input.text())
        self.hit_count_max = int(self.hit_count_max_input.text())
        self.parent().update_sound_paths(self.prepare_sound_path, self.hit_sound_path, self.hold_sound_path, self.release_sound_path)
        
        self.parent().update_hit_count_range(self.hit_count_min, self.hit_count_max)
        self.close()
    # -=-=- Preset Handling -=-=-
        
    # Save Preset
    def save_preset(self):
        preset_name = self.preset_dropdown.currentText()
        preset = [(int(min_input.text()), int(max_input.text()), timer.color) for timer, (min_input, max_input) in zip(self.timers, self.inputs)]
        preset.append(('Hit count', int(self.hit_count_min_input.text()), int(self.hit_count_max_input.text())))

        if preset_name in self.presets:
            reply = QMessageBox.question(self, 'Overwrite preset', f'A preset named "{preset_name}" already exists. Do you want to overwrite it?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return
        else:
            self.preset_dropdown.addItem(preset_name)

        self.presets[preset_name] = preset
        self.last_preset = preset_name

        with open(presets_file, 'w') as f:  # Write the updated presets to the file
            json.dump(self.presets, f)

    # Delete Preset
    def delete_preset(self):
        preset_name = self.preset_dropdown.currentText()  # Get the name of the selected preset
        del self.presets[preset_name]  # Delete the preset
        self.preset_dropdown.removeItem(self.preset_dropdown.currentIndex())  # Remove the preset from the dropdown

        with open(presets_file, 'w') as f:  # Write the updated presets to the file
            json.dump(self.presets, f)

    # Load Preset
    def load_preset(self, index):
        preset_name = self.preset_dropdown.itemText(index)
        preset = self.presets[preset_name]
        for i, timer in enumerate(self.timers):
            preset_timer = preset[i]
            timer.min_time = preset_timer[0]
            timer.max_time = preset_timer[1]
            timer.color = preset_timer[2]
        self.hit_count_min, self.hit_count_max = preset[-1][1], preset[-1][2]  # Load hit_count_min and hit_count_max
        self.update_settings_UI()

    def update_settings_UI(self):
        for timer, (min_input, max_input), color_button in zip(self.timers, self.inputs, self.color_buttons):
            min_input.setText(str(timer.min_time))
            max_input.setText(str(timer.max_time))
            color_button.setStyleSheet(f"background-color: {timer.color};")
        self.hit_count_min_input.setText(str(self.hit_count_min))
        self.hit_count_max_input.setText(str(self.hit_count_max))
        
class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.timer_index = 0
        self.hit_count_min = 2  # Set the minimum hit count
        self.hit_count_max = 3  # Set the maximum hit count
        self.hit_count = 0
        self.timers = [
            Timer('Edging', 120, 240, "rgba(24, 40, 84,1)", ""),
            Timer('Prepare', 10, 10, "rgba(34, 156, 23,1)", "prepare.wav"),
            Timer('Hit', 5, 15, "rgba(173, 5, 39,1)", "hit.wav"),
            Timer('Hold', 10, 20, "rgba(81, 2, 156,1)", "hold.wav"),
            Timer("Release", 5,5, "rgba(4, 51, 181,1)", "release.wav")
        ]
        self.presets = self.load_presets()
        if 'Default' in self.presets:
            self.load_preset('Default')
        else:
            # Load the first preset in the array if 'Default' doesn't exist
            first_preset_name = next(iter(self.presets))
            self.load_preset(first_preset_name)

        if getattr(sys, 'frozen', False):
            # The application is bundled
            base_path = sys._MEIPASS
        else:
            # The application is run from a script
            base_path = os.path.dirname(__file__)

        self.sound_effect = ""
        self.temp_hit_counter = 0
        self.hit_counter = 0
        self.prepare_sound_path = os.path.join(base_path, 'prepare.wav')
        self.hit_sound_path = os.path.join(base_path, 'hit.wav')
        self.hold_sound_path = os.path.join(base_path, 'hold.wav')
        self.release_sound_path = os.path.join(base_path, 'release.wav')
        self.initUI()

    def initUI(self):

        # Top Row Buttons
        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.start_timers)     

        self.settings_button = QPushButton('Settings', self)
        self.settings_button.clicked.connect(self.open_settings)

        self.exit_button = QPushButton('Exit', self)
        self.exit_button.clicked.connect(QApplication.instance().quit) 

        # Current Mode Label
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        font = self.label.font()
        font.setPointSize(28)
        self.label.setFont(font)

        # Countdown Labels
        self.timer_qt = QTimer()
        self.timer_qt.timeout.connect(self.update_timer)
        self.countdown_label = QLabel()
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        self.hitcount_label = QLabel()
        self.hitcount_label.setAlignment(Qt.AlignCenter)

        # Generate Layout - Top row buttons
        vbox = QVBoxLayout()
        hbox = QHBoxLayout()
        hbox.addWidget(self.start_button)
        hbox.addWidget(self.settings_button)
        hbox.addWidget(self.exit_button)
        vbox.addLayout(hbox)
        
        # Generate Layout - 3 shared bottom row widgets
        vbox.addWidget(self.label)
        vbox.addWidget(self.countdown_label)
        vbox.addWidget(self.progress_bar)
        vbox.addWidget(self.hitcount_label)
        
        # Generate Layout - Set the layout
        widget = QWidget()
        widget.setLayout(vbox)
        self.setCentralWidget(widget)
        self.resize(400, 200)
        self.setWindowFlags(Qt.FramelessWindowHint)

    # Dragging window
    def mousePressEvent(self, event):
        self.offset = event.pos()

    def mouseMoveEvent(self, event):
        x=event.globalX()
        y=event.globalY()
        x_w = self.offset.x()
        y_w = self.offset.y()
        self.move(x-x_w, y-y_w)
    # End dragging window
    
    # -=-=- Settings Window -=-=-
    # Open Settings
    def open_settings(self):
        self.settings_window = SettingsWindow(self, self.timers, self.presets, self.hit_count_min, self.hit_count_max)
        self.settings_window.show()
    
    def load_preset(self, preset_name):
        preset = self.presets[preset_name]
        for i, timer in enumerate(self.timers):
            preset_timer = preset[i]
            timer.min_time = preset_timer[0]
            timer.max_time = preset_timer[1]
            timer.color = preset_timer[2]
        self.hit_count_min, self.hit_count_max = preset[-1][1], preset[-1][2]  # Load hit_count_min and hit_count_max
        
    def load_presets(self):
        if not os.path.exists(presets_file):  # If the file does not exist
            os.makedirs(os.path.dirname(presets_file), exist_ok=True)  # Create the directory if it does not exist
            presets = {  # Default presets
                'Default': [(120, 240, "rgba(24, 40, 84,1)"), (10, 10, "rgba(34, 156, 23,1)"), (5, 15, "rgba(173, 5, 39,1)"), (10, 20, "rgba(81, 2, 156,1)"), (5, 5, "rgba(4, 51, 181,1)"), ('Hit count', 1, 3)],
                'Short and Hard': [(120, 240, "rgba(24, 40, 84,1)"), (10, 10, "rgba(34, 156, 23,1)"), (5, 15, "rgba(173, 5, 39,1)"), (10, 20, "rgba(81, 2, 156,1)"), (5, 5, "rgba(4, 51, 181,1)"), ('Hit count', 1, 3)],
                'Long Endurance': [(300, 600, "rgba(24, 40, 84,1)"), (9, 9, "rgba(34, 156, 23,1)"), (10, 10, "rgba(173, 5, 39,1)"), (11, 11, "rgba(81, 2, 156,1)"), (5, 5, "rgba(4, 51, 181,1)"), ('Hit count', 2, 4)],
            }
            with open(presets_file, 'w') as f:  # Create the file and write the default presets
                json.dump(presets, f)
        else:  # If the file exists
            with open(presets_file, 'r') as f:  # Read the presets from the file
                presets = json.load(f)
        return presets
    
    def save(self):
        for timer, (min_input, max_input) in zip(self.timers, self.inputs):
            timer.min_time = float(min_input.text())
            timer.max_time = float(max_input.text())
        with open('presets.json', 'w') as f:  # Write the updated presets to the file
            json.dump(self.presets, f)
        self.close()
    
    def update_hit_count_range(self, min_hits, max_hits):
        self.hit_count_min = min_hits
        self.hit_count_max = max_hits

    def update_sound_paths(self, prepare, hit, hold, release):
        self.prepare_sound_path = prepare
        self.hit_sound_path = hit
        self.hold_sound_path = hold
        self.release_sound_path = release

        # Update the sound_effect attribute of each Timer object
        for timer in self.timers:
            if timer.name == 'Prepare':
                timer.sound_effect = self.prepare_sound_path
            elif timer.name == 'Hit':
                timer.sound_effect = self.hit_sound_path
            elif timer.name == 'Hold':
                timer.sound_effect = self.hold_sound_path
            elif timer.name == 'Release':
                timer.sound_effect = self.release_sound_path

    # -=-=- Timer Handling -=-=-

    # Start Timers
    def start_timers(self):
        print("start_timers called")
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)  # Set the window flag
        self.show()
        self.setWindowOpacity(0.7)
        self.progress_bar.setVisible(True)
        self.settings_button.setEnabled(False)
        self.exit_button.setEnabled(False)
        self.start_button.setText('Stop')
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.stop_timers)
        if self.timer_qt.isActive() == False:
            self.timer_index = 0
        self.timer_qt.start(10)

    def handle_prepare_timer(self):
        self.hit_count = random.randint(self.hit_count_min, self.hit_count_max)  # Select a random hit count
        print(f"Hit count: {self.hit_count}")
        self.label.setText(f'{self.timers[self.timer_index].name} - {self.hit_count} hit')

    def handle_hit_timer(self):
        self.temp_hit_counter += 1
        self.label.setText(f'{self.timers[self.timer_index].name} - {self.temp_hit_counter} of {self.hit_count}')
        self.hit_counter += 1  # Increment the hit counter
        self.hitcount_label.setText(f'Total hits: {self.hit_counter}')

    def handle_hold_timer(self):
        self.label.setText(f'{self.timers[self.timer_index].name} - {self.temp_hit_counter} of {self.hit_count}')

    def handle_release_timer(self):
        if self.temp_hit_counter < self.hit_count:  # If the hit count has not been reached
            self.label.setText(f'{self.timers[self.timer_index].name} - {self.temp_hit_counter} of {self.hit_count}')
            self.timer_index = 2  # Go back to the Hit timer
        else:
            self.label.setText(f'{self.timers[self.timer_index].name}')
            self.timer_index = 0  # Go back to the Edging timer
            self.temp_hit_counter = 0  # Reset the hit counter
        return True  # Indicate that the timer_index has been manually set

    # Map the timer index to the event handler
    timer_event_handlers = {
        1: handle_prepare_timer,
        2: handle_hit_timer,
        3: handle_hold_timer,
        4: handle_release_timer,
    }
    # Update Timer
    def update_timer(self):
        value = self.progress_bar.value()
        self.progress_bar.setInvertedAppearance(True)
        if value > 0:
            self.progress_bar.setValue(value - 1)
            self.countdown_label.setText(f'Time remaining: {value // 100 + 1} seconds')
        else:
            self.timer_qt.stop()
            duration = int(self.timers[self.timer_index].start()) * 100
            sound_effect = self.timers[self.timer_index].sound_effect
            if sound_effect:
                print(f"Playing sound effect: {sound_effect}")
                QSound.play(sound_effect)
            print(f"Switching to timer: {self.timers[self.timer_index].name} with duration: {duration}")
            self.setStyleSheet(f"background-color: {self.timers[self.timer_index].color};")
            self.label.setText(f'{self.timers[self.timer_index].name}')
            self.timer_qt.start(10)
            self.progress_bar.setMaximum(duration)
            self.progress_bar.setValue(duration)

            manually_set = False  # Initialize manually_set to False
            if self.timer_index in self.timer_event_handlers:
                manually_set = self.timer_event_handlers[self.timer_index](self)
            if not manually_set:
                self.timer_index = (self.timer_index + 1) % len(self.timers)  # Go to the next timer
        
        

    # Stop Timers
    def stop_timers(self):
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)  # Clear the window flag
        self.show()
        self.setWindowOpacity(1)
        self.timer_qt.stop()
        self.progress_bar.setValue(0)
        self.label.setText("")
        self.countdown_label.setText("")
        self.progress_bar.setVisible(False)
        self.setStyleSheet("")
        self.settings_button.setEnabled(True)
        self.exit_button.setEnabled(True)
        self.start_button.setText('Start')
        self.start_button.clicked.disconnect()
        self.start_button.clicked.connect(self.start_timers)

def main():
    app = QApplication(sys.argv)
    ex = App()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()