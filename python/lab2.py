"""
This file compiles the code in Web Browser Engineering,
up to and including Chapter 2 (Drawing to the Screen),
"""

from lab1 import request
import socket
import ssl
import tkinter
import re

class Text:
    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "Text('{}'')".format(self.text)

class Tag:
    def __init__(self, tag):
        self.tag = tag

    def __repr__(self):
        return "Tag('{}')".format(self.tag)

def lex(body):
    out = []
    text = ""
    in_tag = False
    for c in body:
        if c == "<":
            in_tag = True
            if text: out.append(Text(text))
            text = ""
        elif c == ">":
            in_tag = False
            out.append(Tag(text))
            text = ""
        else:
            text += c
    if not in_tag and text:
        out.append(Text(text))

    in_body = False
    body_text = ""
    for t in out:
        if isinstance(t, Text):
            if in_body:
                body_text += t.text
        elif re.match(r'^body\s?', t.tag):
            in_body = True
        elif t.tag == "/body":
            in_body = False
    return body_text

WIDTH, HEIGHT = 800, 600
HSTEP, VSTEP = 13, 18

SCROLL_STEP = 100

def layout(text):
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    for c in text:
        display_list.append((cursor_x, cursor_y, c))
        cursor_x += HSTEP
        if cursor_x >= WIDTH - HSTEP or c == "\n":
            cursor_y += VSTEP
            cursor_x = HSTEP
        # breakpoint("layout", display_list)
    return display_list

class Browser:
    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window,
            width=WIDTH,
            height=HEIGHT
        )

        self.canvas.pack()

        self.scroll = 0
        self.min_scroll = 0
        self.max_scroll = 0
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<MouseWheel>", self.mousewheel)

    def load(self, url):
        headers, body = request(url)
        text = lex(body)
        self.display_list = layout(text)
        self.max_scroll = self.display_list[-1][1]
        self.draw()
        tkinter.mainloop()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            # breakpoint("draw")
            if y > self.scroll + HEIGHT: continue
            if y + VSTEP < self.scroll: continue
            self.canvas.create_text(x, y - self.scroll, text=c)

    def scrolldown(self, e):
        self.scroll += SCROLL_STEP
        if self.scroll > self.max_scroll:
            self.scroll = self.max_scroll
        self.draw()

    def scrollup(self, e):
        self.scroll -= SCROLL_STEP
        if self.scroll < self.min_scroll:
            self.scroll = self.min_scroll
        self.draw()

    def mousewheel(self, e):
        if e.delta > 0:
            self.scroll -= SCROLL_STEP
            if self.scroll < self.min_scroll:
                self.scroll = self.min_scroll
            self.draw()
        elif e.delta < 0:
            self.scroll += SCROLL_STEP
            if self.scroll > self.max_scroll:
                self.scroll = self.max_scroll
            self.draw()

if __name__ == "__main__":
    import sys

    Browser().load(sys.argv[1])
    # tkinter.mainloop()
