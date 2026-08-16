#!/usr/bin/env python3
"""Прототип Т9-ввода для CardKB: движок + OSD-окно внизу экрана (GTK3).

Управление (в прототипе — через stdin):
  2-9  — цифра набора
  1    — backspace
  < >  — перебор кандидатов
  Пробел / Enter — подтвердить слово
  q    — выход
  s    — показать/скрыть OSD
"""
import json
import os
import queue
import sys
import threading

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gdk

BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ru_t9.json')


class T9Engine:
    """Движок: последовательность цифр -> кандидаты по частоте."""

    def __init__(self, base_path=BASE):
        with open(base_path, encoding='utf-8') as f:
            self.base = json.load(f)
        self.seq = ''
        self.cands = []
        self.idx = 0

    def add_digit(self, d):
        self.seq += d
        self._recalc()

    def backspace(self):
        if self.seq:
            self.seq = self.seq[:-1]
            self._recalc()

    def next_cand(self):
        if self.cands:
            self.idx = (self.idx + 1) % len(self.cands)

    def prev_cand(self):
        if self.cands:
            self.idx = (self.idx - 1) % len(self.cands)

    def confirm(self):
        """Вернуть выбранное слово (или None) и сбросить набор."""
        word = self.cands[self.idx] if self.cands else None
        self.reset()
        return word

    def reset(self):
        self.seq = ''
        self.cands = []
        self.idx = 0

    def _recalc(self):
        self.cands = self.base.get(self.seq, [])
        self.idx = 0

    # --- вывод ---
    def osd_text(self):
        """Разметка для OSD: выбранный кандидат жирный, остальные серые."""
        if not self.seq:
            return '<span color="#777">Т9: 2-9 буквы, 1 стереть, ←/→ выбор</span>'
        if not self.cands:
            return f'<span color="#f66">нет слова: {self.seq}</span>'
        parts = []
        for i, w in enumerate(self.cands[:8]):
            if i == self.idx:
                parts.append(f'<b><span color="#fff" background="#264" size="large">{w}</span></b>')
            else:
                parts.append(f'<span color="#aaa" size="large">{w}</span>')
        more = f' <span color="#666">+{len(self.cands)-8}</span>' if len(self.cands) > 8 else ''
        return '  '.join(parts) + more


class OSD:
    """GTK-окно-подсказка внизу по центру экрана. Не берёт фокус."""

    def __init__(self):
        self.q = queue.Queue()
        self.visible = False
        self.win = None
        self.label = None
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        Gtk.init(None)
        self.win = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.win.set_decorated(False)
        self.win.set_keep_above(True)
        self.win.set_accept_focus(False)
        self.win.set_can_focus(False)
        self.win.set_skip_taskbar_hint(True)
        self.win.set_skip_pager_hint(True)
        self.win.set_app_paintable(True)
        self.win.set_size_request(480, 48)

        screen = self.win.get_screen()
        sw, sh = screen.get_width(), screen.get_height()
        self.win.move((sw - 480) // 2, sh - 60)

        self.label = Gtk.Label()
        self.label.set_use_markup(True)
        self.label.set_halign(Gtk.Align.CENTER)
        self.win.add(self.label)
        self.win.show_all()
        self.win.hide()

        GLib.timeout_add(40, self._poll)
        Gtk.main()

    def _poll(self):
        try:
            while True:
                text, show = self.q.get_nowait()
                self.label.set_markup(text or '')
                if show and not self.visible:
                    self.win.show()
                    self.visible = True
                elif not show and self.visible:
                    self.win.hide()
                    self.visible = False
        except queue.Empty:
            pass
        return True

    def update(self, markup, show=True):
        self.q.put((markup, show))

    def hide(self):
        self.q.put(('', False))


def main():
    eng = T9Engine()
    osd = OSD()
    osd.update(eng.osd_text())
    print('Т9-прототип. Цифры 2-9, 1=backspace, < > = кандидаты, Пробел/Enter = подтвердить, q = выход.')

    # эмуляция ввода: слово собирается из подтверждённых
    typed = ''
    for line in sys.stdin:
        line = line.rstrip('\n')
        if not line:
            continue
        for ch in line:
            if ch == 'q':
                osd.hide()
                print('ИТОГ:', repr(typed))
                return
            elif ch in '23456789':
                eng.add_digit(ch)
            elif ch == '1':
                eng.backspace()
            elif ch == '<':
                eng.prev_cand()
            elif ch == '>':
                eng.next_cand()
            elif ch in ' \n':
                w = eng.confirm()
                if w:
                    typed += w + ' '
                    print('->', typed.strip())
                elif eng.seq:
                    # нет в словаре — multi-tap-заглушка
                    typed += '? '
            osd.update(eng.osd_text())


if __name__ == '__main__':
    main()
