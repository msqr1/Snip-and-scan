from io import BytesIO
from tkinter import filedialog
from pyzbar import pyzbar
import pygame as pg,os,pyautogui as pag,tkinter as tk,win32api,sys,win32gui,win32con,tempfile,PIL,datetime,win32clipboard,random
pag.FAILSAFE = False
pg.init()
width,height = pag.size()
winsize = (width*1.2//4,height*0.95//5)
center = (width//2-winsize[0]//2,height//2-winsize[1]//2)
centerx,centery = center[0],center[1]
os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (centerx,centery-centery*7//8)
screen = pg.display.set_mode(winsize,pg.RESIZABLE)
icon = pg.transform.smoothscale(pg.image.load('Logo.png').convert(),(32,32))
globaldata = None
dragtool = None
Name = None
gldatatest,thread1 = None,None
pg.display.set_icon(icon)
pg.display.set_caption('Snip and scan')
allsprite = pg.sprite.Group()
ivsprite = pg.sprite.Group()
pgmousepos = pg.mouse.get_pos()
globalpos = pag.position()
hwnd = pg.display.get_wm_info()['window']
name = None
def saveimg(image):
    if image:
        root = tk.Tk()
        root.withdraw()
        img = tk.filedialog.asksaveasfilename(defaultextension='.png',filetypes =[('PNG','.png'),('JPG/JPEG','.jpg'),('TIFF','.tiff'),('TIF','.tif.')],initialfile = f'Screencrop {name}')
        if img:
            image.save(img)
        root.destroy()
def copytoclipboard(var):
    if isinstance(var,str) or isinstance(var,int):
        def retry():
            try:
                var = str(var)
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardText(var)
                win32clipboard.CloseClipboard()
            except Exception:
                retry()
        retry()
    else:
        def retry():
            try:
                output = BytesIO()
                var.convert('RGB').save(output, 'BMP')
                data = output.getvalue()[14:]
                output.close()
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_DIB, data)
                win32clipboard.CloseClipboard()
            except Exception:
                retry()
        retry()
def InstantMinimize(): #Minimize the window instantly regardless of animations settings
    winsize = pg.display.get_window_size()
    hwnd = pg.display.get_wm_info()['window']
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0,0,0),0, win32con.LWA_ALPHA)
    pg.display.set_mode(winsize,pg.NOFRAME)
def InstantMaximize(): #Maximize the window instantly regardless of animations settings
    winsize = pg.display.get_window_size()
    hwnd = pg.display.get_wm_info()['window']
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE,win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE) | win32con.WS_EX_LAYERED)
    win32gui.SetLayeredWindowAttributes(hwnd, win32api.RGB(0,0,0),255, win32con.LWA_ALPHA)
    screen.fill((0,0,0))
    pg.display.set_mode((winsize[0],winsize[1]))
class Cursor(pg.sprite.Sprite):
    def __init__(self):
        pg.mouse.set_pos(globalpos)
        pg.sprite.Sprite.__init__(self)
        self.image = pg.transform.smoothscale(pg.image.load('Cursor.png'),(32,32)).convert()
        self.image.set_colorkey((0,0,0))
        pg.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
        self.rect = self.image.get_rect()
        self.name = type(self).__name__
        self.buttondown = False
        self.pos = None
    def update(self):
        self.rect.centerx,self.rect.centery = pgmousepos[0],pgmousepos[1]
class DragTool(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(0,0,0,0)
        self.pos1,self.pos2 = None,None
        self.gotpos1,self.candrag = False,True
        self.name = type(self).__name__
        self.image = pg.Surface((200,200))
        self.sub = None
        self.subwidth,self.subheight = None,None
        self.zoom = 0
    def pgRectfrom2Pts(self,pos1,pos2):
        rect = pg.Rect(pos1[0],pos1[1],pos2[0]-pos1[0],pos2[1]-pos1[1])
        rect.normalize()
        return rect
    def dragDetection(self):
        global thread1,globalpos,name
        if self.candrag:
            if pg.mouse.get_pressed()[0]:
                if not self.gotpos1:
                    [i.kill() for i in [x for x in allsprite if x.name == 'Cursor']]
                    self.pos1 = pg.mouse.get_pos()
                    [i.kill() for i in [x for x in allsprite if x.name == 'CancelButton']]
                    pg.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
                    self.gotpos1 = True
                self.pos2 = pg.mouse.get_pos()
            if self.pos1 is not None and self.pos2 is not None:
                caprect = self.pgRectfrom2Pts(self.pos1,self.pos2)
                pg.draw.rect(screen,(0,0,0),caprect,2)
                if pg.mouse.get_pressed()[0] == False:
                    if abs(self.pos2[0] - self.pos1[0])==0 or abs(self.pos2[1]-self.pos2[1])==0:
                        allsprite.add(CancelButton())
                        allsprite.add(Cursor())
                        self.pos1,self.pos2 = None,None
                        self.gotpos1,self.candrag = False,True
                    else:
                        global globaldata,hwnd,name
                        pg.draw.rect(screen,(255,255,255),caprect,2)
                        self.sub = screen.subsurface(caprect).copy()
                        pg.display.toggle_fullscreen()
                        pg.display.set_mode((winsize),pg.RESIZABLE)
                        win32gui.ShowWindow(hwnd,win32con.SW_MAXIMIZE)
                        pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
                        pag.moveTo(globalpos)
                        globalpos = None
                        pg.image.save(self.sub,f'{tempfile.gettempdir()}\Screencrop {name}.png')
                        data = pyzbar.decode(PIL.Image.open(f'{tempfile.gettempdir()}\Screencrop {name}.png'))
                        if len(data) > 0:
                            data = data[0].data.decode("utf-8")
                            globaldata = data
                            print(data)
                        allsprite.add(NewButton())
                        allsprite.add(SaveButton())
                        allsprite.add(CopyButton())
                        self.candrag = False
    def update(self):
        global width,height,name
        self.dragDetection()
        if self.sub is not None:
            self.subwidth,self.subheight = self.sub.get_width(),self.sub.get_height()
            for IMGs in [i for i in allsprite if i.name == 'Image']:
                IMGs.kill()
            screen.blit(self.sub,(width//2-self.sub.get_width()//2 ,height//2-self.sub.get_height()//2))
class Image(pg.sprite.Sprite):
    def __init__(self,surface):
        global dragtool
        pg.sprite.Sprite.__init__(self)
        self.image = surface
        self.rect = surface.get_rect()
        self.name = type(self).__name__
        dragtool = DragTool()
        ivsprite.add(dragtool)
class CancelButton(pg.sprite.Sprite):
    def __init__(self):
        global width,height
        pg.sprite.Sprite.__init__(self)
        self.font = pg.font.Font(None,45)
        self.image = self.font.render(' Cancel ',True,(0,0,0),(255,255,0))
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y = width//2-100,20
        self.border = pg.Rect(self.rect.x,self.rect.y,self.rect.width+4,self.rect.height+2)
        self.border.top-=2
        self.border.left-=2
        self.name = type(self).__name__
    def update(self): 
        global pgmousepos,hwnd,candrag,winsize,name
        if self.rect.left<pgmousepos[0]<self.rect.right and self.rect.top<pgmousepos[1]<self.rect.bottom:
            self.image = self.font.render(' Cancel ',True,(255,0,0),(255,255,224))
            if pg.mouse.get_pressed()[0]:
                allsprite.add(NewButton())
                [i.kill() for i in [x for x in allsprite if x.name == 'Image']]
                [i.kill() for i in [x for x in ivsprite if x.name == 'DragTool']]
                [i.kill() for i in [x for x in allsprite if x.name == 'Cursor']]
                pg.mouse.set_cursor(pg.SYSTEM_CURSOR_ARROW)
                os.remove(f'{tempfile.gettempdir()}\Screencrop {name}.png')
                pg.display.toggle_fullscreen()
                pg.display.set_mode(winsize,pg.RESIZABLE)
                pag.moveTo(globalpos)
                self.kill()
        else:
            self.image = self.font.render(' Cancel ',True,(0,0,255),(255,255,0))
        pg.draw.rect(screen,(0,0,0),self.border,2,3)
class NewButton(pg.sprite.Sprite):
    def __init__(self):
        pg.sprite.Sprite.__init__(self)
        self.font = pg.font.Font(None,45)
        self.image = self.font.render(' + New snip ',True,(0,0,0),(245,245,245))
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y = 10,10
        self.border = pg.Rect(self.rect.x,self.rect.y,self.rect.width+4,self.rect.height+2)
        self.border.top-=2
        self.border.left-=2
        self.clicked = False
        self.name = type(self).__name__
    def screenshot(self):
        image = pag.screenshot()
        return image
    def ForegroundWindow(self):
        def DeleteDupes(a_list):
            k = []
            [k.append(i) for i in a_list if i not in k]
            return k
        names = []
        def winEnumHandler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                n = win32gui.GetWindowText(hwnd)  
                if n:
                    names.append(n)
        win32gui.EnumWindows(winEnumHandler, None)
        return list(DeleteDupes(names))
    def update(self):
        global pgmousepos,hwnd,globalpos,name
        if self.rect.left<pgmousepos[0]<self.rect.right and self.rect.top<pgmousepos[1]<self.rect.bottom:
            self.image = self.font.render(' + New snip ',True,(0,0,0),(211,211,211))
            if pg.mouse.get_pressed()[0]:
                allsprite.empty()
                ivsprite.empty()
                InstantMinimize()
                name = f'{hash(datetime.datetime.now().strftime("%m%d%Y%I%M%S"))}'
                self.screenshot().save(f'{tempfile.gettempdir()}\Screencrop {name}.png')
                image = pg.image.load(f'{tempfile.gettempdir()}\Screencrop {name}.png').convert()
                InstantMaximize()
                win32gui.ShowWindow(hwnd,True)
                pg.display.set_mode((0,0),pg.FULLSCREEN)
                allsprite.add(Image(image))
                allsprite.add(CancelButton())
                allsprite.add(Cursor())
                pag.moveTo(globalpos)
                self.kill()
        else:
            self.image = self.font.render(' + New snip ',True,(0,0,0),(245,245,245))
        screen.blit(self.image,self.rect)
        pg.draw.rect(screen,(0,0,0),self.border,2,3)
class SaveButton(pg.sprite.Sprite):
    def __init__(self):
        global width,height,thread1,globaldata
        pg.sprite.Sprite.__init__(self)
        self.image = pg.transform.smoothscale(pg.image.load('SaveButton.png').convert(),(32,32))
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y = width-50,10
        self.image.set_colorkey((0,0,0))
        self.name = type(self).__name__
        self.borderrect = pg.Rect(self.rect.x-1,self.rect.y-1,self.rect.width+1,self.rect.height+1)
    def update(self):
        global pgmousepos,thread1,gldatatest,globaldata
        if self.rect.left<pgmousepos[0]<self.rect.right and self.rect.top<pgmousepos[1]<self.rect.bottom:
            pg.draw.rect(screen,(0,0,0),self.borderrect,2)
            if pg.mouse.get_pressed()[0]:
                saveimg(PIL.Image.open(f'{tempfile.gettempdir()}\Screencrop {name}.png'))
class CopyButton(pg.sprite.Sprite):
    def __init__(self):
        global width,height,globaldata
        pg.sprite.Sprite.__init__(self)
        self.image = pg.transform.smoothscale(pg.image.load('ClipboardButton.png').convert(),(29,29))
        self.rect = self.image.get_rect()
        self.rect.x,self.rect.y = width-90,11
        self.image.set_colorkey((0,0,0))
        self.name = type(self).__name__
        self.borderrect = pg.Rect(self.rect.x-1,self.rect.y-1,self.rect.width+1,self.rect.height+1)
        self.copied_mouse = False
        self.copied_key = False
    def update(self):
        global pgmousepos, globaldata
        if self.rect.left<pgmousepos[0]<self.rect.right and self.rect.top<pgmousepos[1]<self.rect.bottom:
            pg.draw.rect(screen,(0,0,0),self.borderrect,2)
            if pg.mouse.get_pressed()[0] and not self.copied_mouse:
                copytoclipboard(PIL.Image.open(f'{tempfile.gettempdir()}\Screencrop {name}.png'))
                self.copied_mouse = True
            elif pg.mouse.get_pressed()[0] == False:
                self.copied_mouse = False
        if (pg.key.get_pressed()[pg.K_RCTRL] or pg.key.get_pressed()[pg.K_LCTRL]) and pg.key.get_pressed()[pg.K_c] and not self.copied_key:
            copytoclipboard(PIL.Image.open(f'{tempfile.gettempdir()}\Screencrop {name}.png'))
            self.copied_key = True
        elif pg.key.get_pressed()[pg.K_RCTRL] == False and pg.key.get_pressed()[pg.K_LCTRL] == False and pg.key.get_pressed()[pg.K_c] == False:
            self.copied_key = False
allsprite.add(NewButton())
clock = pg.time.Clock()
while True:
    screen.fill((255,255,255))
    allsprite.draw(screen)
    allsprite.update()
    ivsprite.update()
    pgmousepos = pg.mouse.get_pos()
    globalpos = pag.position()
    if dragtool:
        dragtool.zoom = 0
    try:
        def retry():
            global dragtool
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    if os.path.exists(f'{tempfile.gettempdir()}\Screencrop {name}.png'):
                        os.remove(f'{tempfile.gettempdir()}\Screencrop {name}.png')
                    pg.quit()
                    sys.exit()
        retry()
    except KeyboardInterrupt:
        retry()
    pg.display.update()
