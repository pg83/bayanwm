import functools

from libqtile.config import Key, Screen, Group, Drag, Click, EzKey
from libqtile.command import lazy
from libqtile import layout, bar, widget, hook
from libqtile.backend.wayland import InputConfig

mod = 'mod4'
alt = 'mod1'

follow_mouse_focus = True

groups = [
    Group(i) for i in '12345'
]

def it_keys():
    yield Key([mod], 'e', lazy.shutdown())
    yield Key([mod], 'x', lazy.window.kill())

    yield Key([mod], 'Return', lazy.spawn('foot'))
    yield Key([mod], 'd', lazy.spawn('fuzzel'))

    yield Key([mod], 'Left', lazy.group.prev_window())
    yield Key([mod], 'Right', lazy.group.next_window())

    for g in groups:
        yield Key([mod], g.name, lazy.group[g.name].toscreen())


keys = list(it_keys())

widget_defaults = {
    'font': 'sans',
    'fontsize': 24,
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
