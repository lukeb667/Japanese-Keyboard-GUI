# -*- coding: utf-8 -*-
import pygame
import win32gui
import win32con
import ctypes
import os  
import mouse
import time


class TranslationGUI:
    def __init__(self, location:str='top'):
        self.caption = 'Working String:'
        self.running = True
        self.can_click = True
        self.hidden = False
        
        if location != 'top': location = 'bottom'
        self.location = location

        pygame.init()
        pygame.font.init()
        self.font = pygame.font.Font('res/Setofont Regular.ttf', 30)
        user32 = ctypes.windll.user32
        self.msize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        self.screen_x = user32.GetSystemMetrics(0)
        self.screen_y = 40
        self.text = '日本語鍵盤'
        
        self.ico = pygame.image.load('res/lang.png')
        pygame.display.set_icon(self.ico)
        os.environ['SDL_VIDEO_WINDOW_POS'] = str(int(self.msize[0]/2 - self.screen_x/2)) + "," + str(0)
        self.screen = pygame.display.set_mode((self.screen_x, self.screen_y), pygame.NOFRAME)
        pygame.display.set_caption(self.caption)
        self.hwnd = user32.FindWindowW(None, self.caption)
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, int(self.msize[0]/2 - self.screen_x/2), 0, 0, 0, win32con.SWP_NOSIZE)

        
        self.bg = pygame.Surface((self.screen_x, self.screen_y))
        self.bg_color = (255,255,255)
        self.bg.fill(self.bg_color)


    def exit(self):
        self.running = False
        pygame.display.quit()
        os.kill(os.getpid(), 0)
    
    def update_text(self, text):
        self.text = text

    def flash(self, color=[150,220,220]):
        self.bg_color = color

    def hide(self):
        if self.hidden == False:
            self.hidden = True
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, int(self.msize[0]/2 - self.screen_x/2), int(-self.screen_y - 10), 0, 0, win32con.SWP_NOSIZE)
        elif self.hidden == True:
            self.hidden = False
            win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, int(self.msize[0]/2 - self.screen_x/2), int(0), 0, 0, win32con.SWP_NOSIZE)
            # self.text = '日本語'

    def mainloop(self):
        if self.running == True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()
                    return False

            mouse_pos = mouse.get_position()
            self.screen.blit(self.bg,(0,0))

            self.rendered_text = pygame.font.Font.render(self.font, self.text, True, 'BLACK')
            self.screen.blit(self.rendered_text, (self.screen_x/2 - self.rendered_text.get_width()/2, self.screen_y/2 - self.rendered_text.get_height()/2))
            if pygame.mouse.get_pressed()[0]: self.can_click = False
            else: self.can_click = True
            if self.bg_color[0] < 255:
                self.bg_color[0] += 1
            if self.bg_color[1] < 255:
                self.bg_color[1] += 1
            if self.bg_color[2] < 255:
                self.bg_color[2] += 1
            time.sleep(.005)
            self.bg.fill(self.bg_color)
            if self.hidden == False:
                if self.location == 'top':
                    if mouse_pos[1] <= self.screen_y + 50:
                        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, int(self.msize[0]/2 - self.screen_x/2), int(mouse_pos[1] - self.screen_y - 50), 0, 0, win32con.SWP_NOSIZE)
                    else: win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, int(self.msize[0]/2 - self.screen_x/2), 0, 0, 0, win32con.SWP_NOSIZE)
                elif self.location == 'bottom':
                    if mouse_pos[1] >= self.msize[1] - self.screen_y - 50:
                        win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, int(self.msize[0]/2 - self.screen_x/2), int(mouse_pos[1] + 50), 0, 0, win32con.SWP_NOSIZE)
                    else: win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST, int(self.msize[0]/2 - self.screen_x/2), int(self.msize[1] - self.screen_y), 0, 0, win32con.SWP_NOSIZE)
            pygame.display.update()
        else: return False
