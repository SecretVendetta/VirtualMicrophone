import os
import platform
import hashlib
import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from threading import Thread
import json  # Used for settings serialization
from text_to_speech_player import TextToSpeechPlayer  # Ensure this module is defined

# Constants for repeated values
BACKGROUND_COLOR = '#333333'
TEXT_COLOR = 'white'
BUTTON_ACTIVE_COLOR = '#5e5e5e'
WAV_FILE_NAME = "temp_tts_output.wav"
SETTINGS_FILE = "settings.json"

class TextToSpeechGUI:
    def __init__(self, master):
        self.master = master
        self.configure_window()
        self.tts_player = TextToSpeechPlayer()  # Ensure TextToSpeechPlayer is defined
        self.tts_thread = None
        self.clear_text_on_speech_end = False

        # Setting up the cache directory in AppData or a platform-appropriate location
        self.cache_directory = self._get_cache_directory()
        if not os.path.exists(self.cache_directory):
            os.makedirs(self.cache_directory)

        self._setup_styles()

        # Load settings
        self.settings = self._load_settings()

        self._create_checkbox()  # Create the checkbox
        self._setup_widgets()

        # Preload phrases into the cache
        self._preload_phrases()

    def _create_checkbox(self):
        self.show_phrases_var = tk.BooleanVar(value=self.settings.get('show_phrases', True))
        self.show_phrases_checkbox = ttk.Checkbutton(self.master, text="Show Phrases",
                                                     variable=self.show_phrases_var, command=self._toggle_phrases,
                                                     style='Small.TCheckbutton')
        # Reduced padding for a more compact appearance
        self.show_phrases_checkbox.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky="ew")

    def _toggle_phrases(self):
        show_phrases = self.show_phrases_var.get()
        for button in self.buttons:
            if show_phrases:
                button.grid()
            else:
                button.grid_remove()
        self._adjust_window_size()

    def _load_settings(self):
        settings_path = os.path.join(self.cache_directory, SETTINGS_FILE)
        if os.path.exists(settings_path):
            with open(settings_path, 'r') as file:
                try:
                    return json.load(file)
                except json.JSONDecodeError:
                    return {}
        return {}

    def _save_settings(self, settings):
        settings_path = os.path.join(self.cache_directory, SETTINGS_FILE)
        with open(settings_path, 'w') as file:
            json.dump(settings, file)

    def _is_tts_active(self):
        return self.tts_thread is not None and self.tts_thread.is_alive()

    def _get_cache_directory(self):
        app_name = "MyTextToSpeechApp"
        if platform.system() == "Windows":
            cache_dir = os.path.join(os.getenv('APPDATA'), app_name, "Cache")
        else:
            cache_dir = os.path.expanduser(os.path.join("~", ".local", "share", app_name, "Cache"))
        return cache_dir

    def _preload_phrases(self):
        self.cached_phrases = {}
        phrases = ["Hello", "Yes", "No", "Okay", "I need help", "Right here", "Sorry", "Goodbye"]
        for phrase in phrases:
            cached_file = self._get_cached_file(phrase)
            if not os.path.exists(cached_file):
                self.tts_player.save_tts_to_wav(phrase, cached_file)
            self.cached_phrases[phrase] = cached_file

    def _get_cached_file(self, phrase):
        sanitized_phrase = "".join([c for c in phrase if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filename = hashlib.md5(sanitized_phrase.encode()).hexdigest() + ".wav"
        return os.path.join(self.cache_directory, filename)

    def configure_window(self):
        self.master.title("Text to Speech")
        self.master.attributes('-topmost', True)
        self.master.configure(background=BACKGROUND_COLOR)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure('TFrame', background=BACKGROUND_COLOR)
        style.configure('TLabel', background=BACKGROUND_COLOR, foreground=TEXT_COLOR, font=('Arial', 12))
        style.configure('TEntry', background='white', foreground='black', insertbackground='black', font=('Arial', 11))
        style.configure('TButton', background='#4e4e4e', foreground=TEXT_COLOR, font=('Arial', 10), padding=(3, 2))
        style.map('TButton', background=[('active', BUTTON_ACTIVE_COLOR)], foreground=[('active', TEXT_COLOR)])
        style.configure('Small.TCheckbutton', font=('Arial', 8))

        self.master.configure(background=BACKGROUND_COLOR)

    def _setup_widgets(self):
        self._create_label()
        self._create_text_input()
        self._create_checkbox()  # Reposition the checkbox right below the text input
        self._create_button_frame()
        self._adjust_window_size()

    def _create_label(self):
        self.label = ttk.Label(self.master, text="Enter text:")
        self.label.grid(row=0, column=0, columnspan=4, pady=(5, 1), padx=10, sticky="ew")

    def _create_text_input(self):
        self.text_input = ttk.Entry(self.master)
        self.text_input.grid(row=1, column=0, columnspan=4, padx=10, pady=(1, 5), sticky="ew")
        self.text_input.bind("<Return>", self.speak)

    def _create_button_frame(self):
        self.button_frame = ttk.Frame(self.master)
        self.button_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=5, sticky='nsew')
        self.master.grid_rowconfigure(2, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self._create_buttons()

    def _create_buttons(self):
        self.buttons = []
        phrases = ["Hello", "Yes", "No", "Okay", "I need help", "Right here", "Sorry", "Goodbye", "Thank you"]
        for i, phrase in enumerate(phrases):
            button = ttk.Button(self.button_frame, text=phrase, 
                                command=lambda p=phrase: self.speak_word(p), cursor="hand2")
            button.grid(row=i // 3, column=i % 3, padx=(5, 0), pady=(1, 0), sticky="ew")
            self.buttons.append(button)
        self._configure_button_grid()

    def _configure_button_grid(self):
        for j in range(3):
            self.button_frame.grid_columnconfigure(j, weight=1)

    def _add_audio_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.wav *.mp3")])
        if file_path:
            self._create_audio_button(file_path)

    def _create_audio_button(self, file_path):
        file_name = os.path.basename(file_path)
        button = ttk.Button(self.button_frame, text=file_name, 
                            command=lambda: self._play_audio_file(file_path), cursor="hand2")
        button.grid(row=len(self.buttons) // 3, column=len(self.buttons) % 3, 
                    padx=(5, 0), pady=(1, 0), sticky="ew")
        self.buttons.append(button)
        self._configure_button_grid()
        self._adjust_window_size()

    def _adjust_window_size(self):
        self.master.update_idletasks()

        # Base height includes label, text input, and checkbox
        base_height = self.label.winfo_reqheight() + self.text_input.winfo_reqheight() + self.show_phrases_checkbox.winfo_reqheight()

        # Add height of button frame if checkbox is ticked
        additional_height = self.button_frame.winfo_reqheight() if self.show_phrases_var.get() else 0

        # Calculate total height
        total_height = base_height + additional_height

        # Adjust padding based on checkbox state
        padding = 42 if self.show_phrases_var.get() else 30

        # Calculate the required width
        total_width = max(self.text_input.winfo_reqwidth(), self.button_frame.winfo_reqwidth(), self.show_phrases_checkbox.winfo_reqwidth())

        # Set the window size
        self.master.geometry(f"{total_width}x{total_height + padding}")
        self.master.minsize(total_width, total_height + padding)

    def _toggle_buttons(self, state=tk.NORMAL):
        for button in self.buttons:
            button['state'] = state

    def _play_audio_file(self, file_path):
        try:
            self.tts_player.play_audio(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {e}")

    def speak(self, event=None):
        text = self.text_input.get()
        if text and not self._is_tts_active():
            self._toggle_buttons(tk.DISABLED)
            self.text_input['state'] = tk.DISABLED
            self.tts_thread = Thread(target=self._process_speech, args=(text,))
            self.tts_thread.start()
            self.clear_text_on_speech_end = True

    def speak_word(self, word):
        if not self._is_tts_active():
            self._toggle_buttons(tk.DISABLED)
            self.text_input['state'] = tk.DISABLED
            self.tts_thread = Thread(target=self._initiate_speech, args=(word,))
            self.tts_thread.start()

    def _initiate_speech(self, text):
        cached_file = self.cached_phrases.get(text, None)
        if cached_file:
            self._play_audio_file_thread(cached_file)
        else:
            self._process_speech(text)

    def _play_audio_file_thread(self, file_path):
        try:
            self.tts_player.play_audio(file_path)
        except Exception as e:
            self.master.after(0, lambda: self._display_error(str(e)))
        finally:
           
            self.master.after(0, self._after_speech_cleanup)

    def _process_speech(self, text):
        try:
            wav_file_path = os.path.join(self.cache_directory, WAV_FILE_NAME)
            self.tts_player.save_tts_to_wav(text, wav_file_path)
            self._play_audio_file_thread(wav_file_path)
        except Exception as e:
            self.master.after(0, lambda: self._display_error(str(e)))

    def _display_error(self, message):
        messagebox.showerror("Error", f"An error occurred: {message}")

    def _after_speech_cleanup(self):
        self._toggle_buttons(tk.NORMAL)
        self.text_input['state'] = tk.NORMAL
        if self.clear_text_on_speech_end:
            self.text_input.delete(0, tk.END)
            self.clear_text_on_speech_end = False

    def _enable_text_input(self):
        self.text_input['state'] = tk.NORMAL

if __name__ == "__main__":
    root = tk.Tk()
    app = TextToSpeechGUI(root)
    root.mainloop()
