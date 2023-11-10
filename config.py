import os
import time
import signal
import functools
import subprocess

from libqtile import layout, bar, widget, hook
from libqtile.config import Key, Screen, Group, Drag, Click, EzKey
from libqtile.command import lazy
from libqtile.command.base import expose_command
from libqtile.layout.base import _SimpleLayoutBase
from libqtile.backend.wayland import InputConfig
from libqtile.widget.base import ThreadPoolText


mod = 'mod4'
alt = 'mod1'
term = 'foot'
follow_mouse_focus = True

class I3Status(ThreadPoolText):
    def poll(self):
        try:
            return self.proc.stdout.readline().decode().strip()
        except Exception as e:
            time.sleep(1)
            self.proc = subprocess.Popen(['i3status'], shell=False, stdout=subprocess.PIPE)
            return 'restart'

top_bar = bar.Bar([
    widget.WindowName(),
    I3Status(text='', update_interval=0),
], 48)

screens = [
    Screen(top=top_bar),
]

groups = [Group('1', spawn=[term, 'telegram-desktop', 'epiphany'])] + [
    Group(i) for i in '2345'
]

def it_keys():
    yield Key([mod], 'e', lazy.shutdown())
    yield Key([mod], 'x', lazy.window.kill())

    yield Key([mod], 'Return', lazy.spawn(term))
    yield Key([mod], 'd', lazy.spawn('fuzzel'))

    yield Key([mod], 'Left', lazy.group.prev_window())
    yield Key([mod], 'Right', lazy.group.next_window())

    for g in groups:
        yield Key([mod], g.name, lazy.group[g.name].toscreen())

    for i in range(1, 6):
        yield Key(['mod1', 'control'], f'F{i}', lazy.core.change_vt(i))

keys = list(it_keys())

class Bayan(_SimpleLayoutBase):
    def __init__(self, **config):
        _SimpleLayoutBase.__init__(self, **config)
        self.prev = None

    def layout(self, windows, screen_rect):
        windows = [x for x in windows if x in self.clients]

        for i in windows:
            if not i.has_focus:
                self.configure(i, screen_rect)

        for i in windows:
            if i.has_focus:
                i.bring_to_front()
                self.configure(i, screen_rect)

    def add_client(self, client):
        return super().add_client(client, 1)

    def it_cur_idx(self):
        idx = self.clients.current_index

        yield idx
        yield idx + self.off

    def get_client(self, i):
        n = len(self.clients)

        if i < 0:
            return self.get_client(i + n)

        return self.clients[i % n]

    def it_cur(self):
        for i in sorted(frozenset(self.it_cur_idx())):
            try:
                yield self.get_client(i)
            except IndexError:
                pass

    def cur(self):
        if len(self.clients) < 3:
            return [x for x in self.clients]

        return list(self.it_cur())

    def configure(self, client, screen_rect):
        if self.prev is None:
            self.off = 1
        else:
            d = self.clients.current_index - self.prev

            if d == 1:
                self.off = -1
            elif d == -1:
                self.off = 1
            elif d > 0:
                self.off = 1
            elif d < 0:
                self.off = -1

        self.prev = self.clients.current_index

        vp = self.cur()

        if client in vp:
            x = screen_rect.x
            y = screen_rect.y
            w = screen_rect.width
            h = screen_rect.height

            bw = 8

            cnt = len(vp)
            idx = vp.index(client)

            dw = (w - (cnt + 1) * bw) // cnt

            x1 = x + (dw + bw) * idx
            y1 = y

            client.place(x1, y1, dw, h - bw * 2, bw, '#881111' if client.has_focus else '#220000', margin=0)
            client.unhide()
        else:
            client.hide()

layouts = [
    Bayan(),
]

widget_defaults = {
    'font': 'sans',
    'fontsize': 32,
    'padding': 6,
    'foreground': 'a0a0a0',
}

wl_input_rules = {
    '*': InputConfig(
        natural_scroll=True,
        tap=True,
        kb_layout='us,ru',
        kb_options='grp:caps_toggle,grp:switch,ctrl:menu_rctrl',
    ),
}

@hook.subscribe.shutdown
def fast_exit():
    os.kill(0, signal.SIGKILL)
