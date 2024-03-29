import os
import json
import time
import queue
import signal
import threading
import functools
import subprocess

import palettable

from libqtile import layout, bar, widget, hook
from libqtile.config import Key, Screen, Group, Drag, Click, EzKey
from libqtile.command import lazy
from libqtile.command.base import expose_command
from libqtile.layout.base import _SimpleLayoutBase
from libqtile.backend.wayland import InputConfig
from libqtile.widget.base import ThreadPoolText

colors = palettable.cartocolors.diverging.Earth_5.hex_colors
colors = palettable.cartocolors.qualitative.Antique_5.hex_colors

mod = 'mod4'
alt = 'mod1'
term = 'alacritty'
follow_mouse_focus = True

where = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))

class AsyncRun:
    def __init__(self, cmd):
        self.cmd = cmd
        self.queue = queue.Queue(maxsize=1)

    def run(self):
        while True:
            try:
                self.cycle()
            except Exception as e:
                self.queue.put(f'command error: {e}')
                time.sleep(1)

    def cycle(self):
        self.queue.put('start')

        proc = subprocess.Popen(self.cmd, shell=False, stdout=subprocess.PIPE)

        while True:
            line = proc.stdout.readline().decode().strip()
            self.queue.put(line)

    def start(self):
        threading.Thread(target=self.run, daemon=True).start()

        return self.queue

def xml_escape(s):
    s = s.replace("&", "&amp;")
    s = s.replace("<", "&lt;")
    s = s.replace(">", "&gt;")
    s = s.replace("\"", "&quot;")
    s = s.replace("'", "&apos;")

    return s

def col(s, color):
    if color:
        return f'<span foreground="{color}">{s}</span>'

    return s

def get_color_for(name):
    return {
        'battery': colors[1],
        'disk_info': colors[2],
        'memory': colors[3],
        'tztime': colors[4],
        '#00FF00': colors[0],
    }.get(name, None)

def remap_color(c):
    while n := get_color_for(c):
        c = n

    return c

def to_pango_f(f):
    t = xml_escape(f['full_text'])

    if 'color' in f:
        c = f['color']
    elif color := get_color_for(f['name']):
        c = color

    return col(t, remap_color(c))

def to_pango(s):
    return col(' | ', 'white').join(to_pango_f(f) for f in json.loads(s))

class I3Status(ThreadPoolText):
    def poll_1(self):
        while True:
            try:
                return self.queue.get()
            except AttributeError:
                self.queue = AsyncRun(['i3status', '-c', os.path.join(where, 'i3.config')]).start()

    def poll_2(self):
        while True:
            l = self.poll_1()

            if l.startswith('[{'):
                return to_pango(l)

            if l.startswith(',[{'):
                return to_pango(l[1:])

            if 'command error' in l:
                return col(xml_escape(l), 'red')

    def poll(self):
        try:
            return self.poll_2()
        except Exception as e:
            return xml_escape(str(e))

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
