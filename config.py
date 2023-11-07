import functools

from libqtile.config import Key, Screen, Group, Drag, Click, EzKey
from libqtile.command import lazy
from libqtile import layout, bar, widget, hook
from libqtile.backend.wayland import InputConfig

mod = 'mod4'
alt = 'mod1'

term = 'foot'

follow_mouse_focus = True

top_bar = bar.Bar([
    widget.Prompt(),
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

layouts = [
    layout.Max(),
]

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
