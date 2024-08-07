# Japanese-Keyboard-GUI
Translate English/Latin syllables to equivalent Japanese Hiragana or Katakana characters

INSTALLATION
1. Ensure you are on a Windows OS
2. Ensure [Python](https://www.python.org/downloads/) is installed on your machine
3. Extract the repository to a folder of your choice
4. Install `requirements.txt` by running `pip install -r requirements.txt` in the installation folder 
5. Run `build-win.bat` in the installation folder
6. A functioning .exe file should now be found in the newly created `dist` folder

DESCRIPTION

This program uses the keyboard module (with modifications) to identify when a typed string matches to a Japanese character based on a dictionary of corresponding phonetic moras or syllables. When a match is identified, the typed string will be replaced with the Japanese character. E.g., typing 'ka' while the program is running will type 'か' instead of the Latin characters. The program can be switched between Hiragana and Katakana via the default hotkey `shift+space`, or can be toggled on/off entirely with `ctrl+space`. Pressing `alt+j` at any time will terminate the program. 

The program suppresses physical keystrokes, and includes a GUI to display what you are currently typing. The GUI can be enabled/disabled with the default hotkey `shift+f1`. Queued keystrokes will be sent after a configurable delay (default 5 seconds), whereafter the script will call an appropriate number of backspace keystrokes for a matched translation key.

Note that for some duplicate phonetic equivalents, what to input for a desired output may not be perfectly intuitive. Looking through the translation dictionary is recommended. 

Kanji translations can be supported - even multiple phonetic equivalents, if the dictionary is configured correctly. To add Kanji keys, copy the Kanji you're adding a translation for to the clipboard, then press the default hotkey `shift+f2`. The GUI will then prompt you to add a key for the clipboard data.

Default hotkeys can be modified via the `config.ini` file.

