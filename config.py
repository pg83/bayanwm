import functools

from libqtile import layout, bar, widget, hook
from libqtile.config import Key, Screen, Group, Drag, Click, EzKey
from libqtile.command import lazy
from libqtile.command.base import expose_command
from libqtile.layout.base import _SimpleLayoutBase
from libqtile.backend.wayland import InputConfig

mod = 'mod4'
alt = 'mod1'

term = 'foot'

follow_mouse_focus = True

top_bar = bar.Bar([
    widget.WindowName(foreground="a0a0a0"),
    widget.Notify(),
    widget.Clock(),
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
        return list(self.it_cur())

    def configure(self, client, screen_rect):
        if client not in self.clients:
            return

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

            idx = vp.index(client)

            dx1 = int(idx * w / len(vp))
            dx2 = int((idx + 1) * w / len(vp))

            client.place(x + dx1 + 2, y + 2, dx2 - dx1 - 4, h - 4, 2, '#0000ff' if client.has_focus else '#000000', margin=2)
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
}

wl_input_rules = {
    '*': InputConfig(
        natural_scroll=True,
        tap=True,
        kb_layout='us,ru',
        kb_options='grp:caps_toggle,grp:switch,ctrl:menu_rctrl',
    ),
}
