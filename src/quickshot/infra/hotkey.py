from __future__ import annotations

from typing import Callable

from pynput import keyboard


class GlobalHotkeyListener:
    def __init__(self, hotkey: str, on_press: Callable[[], None]) -> None:
        self._hotkey = keyboard.HotKey(keyboard.HotKey.parse(hotkey), on_press)

    def run(self) -> None:
        def for_canonical(fn):
            return lambda key: fn(listener.canonical(key))

        with keyboard.Listener(
            on_press=for_canonical(self._hotkey.press),
            on_release=for_canonical(self._hotkey.release),
        ) as listener:
            listener.join()
