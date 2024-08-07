# -*- coding: utf-8 -*-
import src.modified_keyboard as keyboard 
import src.lang_gui as tt # GUI handler
import win32clipboard # For adding Kanji keys
import configparser # For reading the config file
import os
from threading import Timer 


class gv:
    running = True # Indicates when the program should stop 
    hirigana_mode = True  # Which language to translate 
    katakana_mode = False  # Which language to translate
    translate_bool = True  # Whether or not to translate 
    adding_kanji = False # Whether normal rules should be deferred so as to add a Kanji key 
    processed_keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '/', '-', '~', '[', ']', ',', '.', 'space', 'shift', 'ctrl', 'alt', 'enter', 'backspace', 'left', 'right', 'up', 'down', 'tab', 'delete']

    # Try to read the config.ini file. If there is no such file, or any error with the values, use the listed default parameteres
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')

        translation_gui = tt.TranslationGUI(config.get('default', 'gui_location'))
        toggle_gui_hotkey = config.get('default', 'toggle_gui_hotkey')
        add_kanji_hotkey = config.get('default', 'add_kanji_hotkey')
        switch_hotkey = config.get('default', 'switch_hotkey')
        toggle_hotkey = config.get('default', 'toggle_hotkey')
        exit_hotkey = config.get('default', 'exit_hotkey')
        reveal_delay = config.getfloat('default', 'latin_reveal_delay') 
    except:
        translation_gui = tt.TranslationGUI()
        toggle_gui_hotkey = 'shift+f1'
        add_kanji_hotkey = 'shift+f2'
        switch_hotkey = 'shift+space'
        toggle_hotkey = 'ctrl+space' 
        exit_hotkey = 'ctrl+shift+f1'
        reveal_delay = 5.0

class _Helpers():
    timer_thread = None
    def load_translation_dict(): # Load the dictionary txt file. The file will be interpretted as a python dictionary
        with open("src/ja_translation_dict.txt", "r", encoding="utf-8") as file:
            file_text = file.read()
            return eval(file_text)

    def add_hooks(): # Add the relevent keys to the keyboard module's listener, and supress the keystrokes
        for k in gv.processed_keys: keyboard.hook_key(k, callback=lambda e: _Language.process_input(e), suppress=True)

    def remove_hooks(): # Remove the keyboard module's listeners so that the keyboard acts as expected
        keyboard._listener.start_if_necessary()
        keyboard._listener.blocking_keys.clear()
        keyboard._listener.nonblocking_keys.clear()
        del keyboard._listener.blocking_hooks[:]
        del keyboard._listener.handlers[:]

    def add_hotkeys(api_exit_func):
        _Helpers.api_exit_func = api_exit_func 
        keyboard.add_hotkey(gv.switch_hotkey, lambda: TranslationAPI.switch()) # Trigger the hirigana/katakana switch
        keyboard.add_hotkey(gv.toggle_hotkey, lambda: TranslationAPI.enable_disable()) # Enable/disable translation while still running the script
        keyboard.add_hotkey(gv.add_kanji_hotkey, lambda: TranslationAPI.add_kanji_key()) # Add a kanji / latin pair
        keyboard.add_hotkey(gv.toggle_gui_hotkey, lambda: _Helpers.toggle_gui()) # Hide/reveal the gui
        keyboard.add_hotkey(gv.exit_hotkey, lambda: api_exit_func()) 

    def toggle_gui(): # Hide/reveal the gui
        if gv.translate_bool == True:
            gv.translation_gui.hide()

    def reset_latin(): # Set the queued Latin to an empty string. Called when resetting or when translation is executed. 
        _Language.typed_latin = ''
        _Language.latin_to_type = ''
        _Language.displayed_string = ''
        gv.translation_gui.update_text(_Language.displayed_string)

    def start_reveal_timer(delay): # Start a threaded timer to track when queued Latin should be typed
        _Helpers.timer_thread = Timer(delay, function=lambda: _Helpers.timer_trigger(delay))
        _Helpers.timer_thread.start() 

    def timer_trigger(delay): # Function called when reveal timer elapses. Types Latin without updating display string. 
        for c in _Language.latin_to_type:
            try: keyboard._os_keyboard.type_unicode(c)
            except: keyboard.send(c)
            _Language.typed_latin += c 
        _Language.latin_to_type = ''
        _Language.working_string = _Language.typed_latin

    def reset_timer(delay): # Reset the reveal timer.
        if _Helpers.timer_thread != None and _Language.input_modifiers == []:
            _Helpers.timer_thread.cancel()
        _Helpers.start_reveal_timer(delay)

    def update_displayed_text(): # Set the text in the GUI to the working string
        if _Language.working_string != '':
            _Language.displayed_string = _Language.working_string 
            gv.translation_gui.update_text(_Language.displayed_string)


class _Language():
    active_kanji_keys = [] # Contains a list of Kanji keys to cycle through if they have the same latin
    input_modifiers = [] # List of active modifier keys
    kanji_index = 0 # Which of the active Kanji keys are we using
    working_string = '' # String the program is currently processing
    latin_to_type = '' # Latin characters to be revealed after the delay timer
    typed_latin = '' # Latin characters that have already been revealed. Tracked so that backspace can be called when translated.
    displayed_string = '' # The string displayed in the program GUI
    
    new_kanji_key = '' # Variable to hold a new Kanji addition's Latin key
    new_kanji_translation = '' # Variable to hold the new Kanji itself. Grabbed from the system clipboard. 

    ja_translation_dict = _Helpers.load_translation_dict() # Dictionary of Hirigana, Katakana, and Kanji

    def get_valid_kanji(): # Get all valid Kanji keys for the current working string
        _Language.reset_kanji()
        _Language.active_kanji_keys.append(_Language.working_string)
        for key in _Language.ja_translation_dict['<KANJI>']:
            if _Language.working_string + '-' in key and key != _Language.working_string:
                _Language.active_kanji_keys.append(key)

    def cycle_valid_kanji(): # On space, cycle between the valid Kanji keys by calling backspace enough times to delete the current and writing the next
        for c in range(len(_Language.ja_translation_dict['<KANJI>'][_Language.active_kanji_keys[_Language.kanji_index]][0])):
            keyboard.send('backspace')
        try: 
            _Language.kanji_index += 1
            keyboard.write(_Language.ja_translation_dict['<KANJI>'][_Language.active_kanji_keys[_Language.kanji_index]][0])
        except IndexError: 
            _Language.kanji_index = 0
            keyboard.write(_Language.ja_translation_dict['<KANJI>'][_Language.active_kanji_keys[_Language.kanji_index]][0])
        _Language.displayed_string = _Language.ja_translation_dict['<KANJI>'][_Language.active_kanji_keys[_Language.kanji_index]][0]
        gv.translation_gui.update_text(_Language.displayed_string)
        gv.translation_gui.flash([180,220,220]) 
    
    def reset_kanji(): # Clear the active Kanji elements
        _Language.active_kanji_keys = []
        _Language.kanji_index = 0

    def set_working_string(text): # Set the program's working string to the passed text
        _Language.working_string = text
        
    def execute_translation(jp_symbols): # Execute a translation based on the translation mode 
        if gv.translate_bool == True:
            if type(jp_symbols) == list:
                # Delete any typed Latin
                for c in _Language.typed_latin:
                    keyboard.send('backspace')

                # Reset strings
                _Language.typed_latin = ''
                _Language.latin_to_type = ''

                # Type the desired symbols 
                if len(jp_symbols) == 1 or gv.hirigana_mode == True: # length check ensures that a non-existant index isn't called
                    for c in jp_symbols[0]:
                        keyboard._os_keyboard.type_unicode(c)
                    _Language.displayed_string = jp_symbols[0]

                elif gv.katakana_mode == True: 
                    for c in jp_symbols[1]:
                        keyboard._os_keyboard.type_unicode(c)
                    _Language.displayed_string = jp_symbols[1]
                
                # Indicate a translation has occured
                gv.translation_gui.update_text(_Language.displayed_string)
                gv.translation_gui.flash([180,220,220])

    def handle_kanji_cycle(event): # Cycle between valid Kanji translations on space
        if event.name != 'space': _Language.reset_kanji() ; return False
        elif event.name == 'space' and len(_Language.active_kanji_keys) > 1: _Language.cycle_valid_kanji() ; return True

    def handle_hotkeys(event):
        if event.modified == gv.switch_hotkey: 
            TranslationAPI.switch()
            return True
        elif event.modified == gv.toggle_hotkey: 
            TranslationAPI.enable_disable()  
            return True
        elif event.modified == gv.exit_hotkey:
            _Helpers.api_exit_func()
            return True
        else: return False

    def handle_enter(event):
        if event.name == 'enter':
            if _Language.latin_to_type == '': keyboard.send(event.modified) ; _Language.set_working_string('') ; _Helpers.reset_latin()
            else: keyboard.write(_Language.latin_to_type) ; _Language.typed_latin = _Language.latin_to_type ; _Language.latin_to_type = ''
            _Helpers.update_displayed_text()
            return True
        else: return False

    def handle_backspace(event): 
        if event.name == 'backspace':
            if _Language.displayed_string != _Language.working_string: _Language.displayed_string = '' ; gv.translation_gui.update_text(_Language.displayed_string)
            if _Language.typed_latin != '' and _Language.working_string != '': _Language.typed_latin = _Language.typed_latin[:-1] ; _Language.working_string = _Language.working_string[:-1] ; keyboard.send(event.modified)
            elif _Language.working_string != '': _Language.working_string = _Language.working_string[:-1]; _Language.latin_to_type = _Language.latin_to_type[:-1]
            else: keyboard.send(event.modified) ; _Helpers.update_displayed_text() ; _Language.displayed_string = _Language.displayed_string[:-1] ; return True 
            _Helpers.update_displayed_text()
            if _Language.displayed_string != _Language.working_string: _Language.displayed_string = '' ; gv.translation_gui.update_text(_Language.displayed_string)
            return True
        else: return False
        
    def handle_modded_event(event):
        if event.name != event.modified: 
            if 'ctrl' not in event.modified and 'shift' in event.modified and len(event.modified.removeprefix('shift+')) == 1:
                _Language.handle_translation(event)
                return True
            else: 
                _Language.working_string = ''
                keyboard.send(event.modified)
                _Helpers.reset_latin()
                _Helpers.update_displayed_text()    
                return True
        
    def handle_translation(event):
        if len(event.name) == 1:
            _Language.working_string += event.name
            _Language.latin_to_type += event.name 

            if _Language.working_string in _Language.ja_translation_dict.keys(): # Is there a match in the main dictionary 
                _Helpers.reset_timer(gv.reveal_delay + 1) 
                _Language.execute_translation(_Language.ja_translation_dict[_Language.working_string])
                _Language.set_working_string('')

            elif _Language.working_string in _Language.ja_translation_dict['<DOUBLES>'].keys(): # Is there a match in the doubles dictionary
                _Helpers.reset_timer(gv.reveal_delay + 1) 
                _Language.displayed_string = _Language.ja_translation_dict['<DOUBLES>'][_Language.working_string]
                _Language.execute_translation( _Language.ja_translation_dict['<DOUBLES>'][_Language.working_string])
                _Language.working_string = _Language.working_string[-1]
                _Language.latin_to_type = _Language.working_string
                _Language.displayed_string += _Language.working_string
                gv.translation_gui.update_text(_Language.displayed_string)
            else:
                _Helpers.update_displayed_text()
            return True
        else: return False 
        
    def handle_space(event):
        if event.modified == 'space' or event.modified == 'ctrl+backspace':
            if _Language.working_string == '': keyboard.send(event.modified)
            else: _Language.set_working_string('') ; _Helpers.reset_latin() ; 
            _Helpers.update_displayed_text()  
            return True

    def handle_kanji_match(event):
        if event.name == 'space' and _Language.working_string in _Language.ja_translation_dict['<KANJI>'].keys(): # Is there a match in the Kanji dictionary
            _Language.get_valid_kanji()
            _Language.execute_translation(_Language.ja_translation_dict['<KANJI>'][_Language.working_string])
            _Language.set_working_string('') 
            _Helpers.update_displayed_text()
            return True

    def handle_overflow(event):
        if len(event.name) > 1: keyboard.send(event.name) ; _Language.set_working_string('') ; _Helpers.reset_latin() ; _Helpers.update_displayed_text() ; return True
        else: return False

    def handle_kanji_addition(event):
        def finalize(msg="Kanji Added", color=[200,255,200]):
            _Language.new_kanji_key = '' 
            _Language.new_kanji_translation = '' 
            gv.adding_kanji = False
            gv.translation_gui.update_text(msg) 
            gv.translation_gui.flash(color)

        if gv.adding_kanji == True:
            if len(event.name) == 1:
                _Language.new_kanji_key += event.name
                gv.translation_gui.update_text('/' + _Language.new_kanji_key + ': ' + _Language.new_kanji_translation) 
            elif event.name == 'backspace':
                _Language.new_kanji_key = _Language.new_kanji_key[:-1]
                gv.translation_gui.update_text('/' + _Language.new_kanji_key + ': ' + _Language.new_kanji_translation) 
            elif event.name == 'enter':
                with open('src/ja_translation_dict.txt', 'r', encoding='utf-8') as file:
                    lines = file.readlines() 
                    has_key = 0

                    # Ensure no empty key 
                    if _Language.new_kanji_key == '':
                        finalize('Invalid Key', [255,200,200]) 
                        return True

                    for line in lines:
                        if "'/" + _Language.new_kanji_key + "':" in line or "'/" + _Language.new_kanji_key + "-" in line: 
                            if "['" + _Language.new_kanji_translation + "']" in line: 
                                finalize('Dictionary Already Contains Pair', [255,255,200]) 
                                return True
                            else: has_key += 1 
                    for line in lines:
                        if '<KANJI>' in line:
                            if has_key == 0:
                                lines.insert(lines.index(line)+1, '\n\t\t' + "'/" + _Language.new_kanji_key + "':" +  "['" + _Language.new_kanji_translation + "'],") 
                            else: lines.insert(lines.index(line)+1, '\n\t\t' + "'/" + _Language.new_kanji_key + "-" + str(has_key) + "':" +  "['" + _Language.new_kanji_translation + "'],") 

                with open('src/ja_translation_dict.txt', 'w', encoding='utf-8') as file:
                    for line in lines: 
                        file.writelines(line) 
                finalize()
            return True
            
    def pre_process_event(event):
        event.input_modifiers = []
        
        # Return True if the key pressed is a modifier and ensure that the key is released properly. 
        if keyboard.is_modifier(event.name) == True:
            if event.event_type == 'up': keyboard.send(event.name, False, True) 
            return True  
        
        # Format modifiers 
        else: 
            if keyboard.is_pressed('ctrl') or keyboard.is_pressed('right ctrl'): event.input_modifiers.append('ctrl+') 
            else: keyboard.send('ctrl', False, True) ; 
            if keyboard.is_pressed('shift') or keyboard.is_pressed('right shift'): event.input_modifiers.append('shift+') 
            else: keyboard.send('shift', False, True) ; 
            if keyboard.is_pressed('alt') or keyboard.is_pressed('right alt'): event.input_modifiers.append('alt+') 
            else: keyboard.send('alt', False, True) ; 
            event.modified = ''.join(event.input_modifiers) + event.name
            return event.modified 

    def process_input(event): # The event is keyboard's 'KeyboardEvent'

        # Main logic block. If the key event is handled by a function, that function will return True. Otherwise, the next function is checked. 
        # The order of these functions is critical - hotkeys need to take priority over translations, for example.  
        # Modifier keys themselves are not processed, but instead are appended to the modifiers.

        event.modified = _Language.pre_process_event(event) # Format modifiers correctly and check if current key is a modifier
        if event.modified == True: return # Will be true if the key pressed is a modifier

        if event.event_type == 'down':
            if _Language.handle_kanji_addition(event) == True: return
            if _Language.handle_kanji_cycle(event) == True: return 
            if _Language.handle_hotkeys(event) == True: return
            if _Language.handle_modded_event(event) == True: return # Checks if the event is just a shifted key, and sends to main translation if case. Otherwise, sends the modded event.
            if _Language.handle_kanji_match(event) == True: return
            if _Language.handle_enter(event) == True: return
            if _Language.handle_backspace(event) == True: return 
            if _Language.handle_space(event) == True: return 
            if _Language.handle_translation(event) == True: return # Main translation function. 
            if _Language.handle_overflow(event) == True: return # Checks for unhandled keys and sends them unmolested if caught
            raise ValueError('Unhandled Key: "' + event.name + '"')
        elif event.event_type == 'up': 
            _Helpers.reset_timer(gv.reveal_delay) 
            return

class TranslationAPI():
    def __init__(self) -> None:
        self.running = True
        if gv.reveal_delay < .05: gv.reveal_delay = .05 # Minimum reveal timer. A timer quicker than this can confuse the system and cause unwanted key calls.

        # Add keyboard hooks and listeners
        _Helpers.add_hotkeys(self.exit)
        _Helpers.add_hooks() 

        while self.running == True:
            gv.translation_gui.mainloop()
            if gv.translation_gui.running == False: 
                self.running = False 
        
        # Exit Code
        keyboard.remove_all_hotkeys()
        _Helpers.remove_hooks()
        gv.translation_gui.exit()
        os.kill(os.getpid(), 0)
        
    def exit(self):
        self.running = False
    
    def add_kanji_key():
        if gv.adding_kanji == False:
            try:
                win32clipboard.OpenClipboard()
                _Language.new_kanji_translation = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                if "'" not in _Language.new_kanji_translation:
                    gv.adding_kanji = True 
                    gv.translation_gui.update_text("Adding key for: " + _Language.new_kanji_translation) 
                else:
                    _Language.new_kanji_translation = ''
                    gv.translation_gui.update_text('Clipboard Data Incompatable') 
                    gv.translation_gui.flash([255,200,200])
            except:
                gv.translation_gui.update_text('Clipboard Data Incompatable')
                gv.translation_gui.flash([255,200,200])
        
        # If add hotkey is called a second time, abort the process. 
        elif gv.adding_kanji == True: 
            _Language.new_kanji_key = ''
            _Language.new_kanji_translation = '' 
            gv.translation_gui.update_text('Process Aborted')
            gv.translation_gui.flash([255,200,200])
            gv.adding_kanji = False

    def switch():  # Switch between hirigana and katakana translation modes. 
        if gv.hirigana_mode == True: gv.hirigana_mode = False ; gv.katakana_mode = True ; _Language.displayed_string = 'カタカナ'
        elif gv.katakana_mode == True: gv.katakana_mode = False ; gv.hirigana_mode = True ; _Language.displayed_string = '平仮名'
        gv.translation_gui.update_text(_Language.displayed_string)

    def enable_disable():  # Enable/disable the translation function
        if gv.translate_bool == True: gv.translate_bool = False ; _Helpers.remove_hooks()
        elif gv.translate_bool == False: gv.translate_bool = True ; _Helpers.add_hooks()
        _Language.set_working_string('')
        _Helpers.reset_latin()
        
        gv.translation_gui.hide()

main = TranslationAPI()



