"""
This file compiles the code in Web Browser Engineering,
up to and including Chapter 1 (Downloading Web Pages)
"""

import socket
import ssl
import sys

redirects_times = 0

def request(url):
    scheme, url = url.split("://", 1)
    assert scheme in ["http", "https"], \
        "Unknown scheme {}".format(scheme)

    if ("/" in url):
        host, path = url.split("/", 1)
        path = "/" + path
    else:
        host = url
        path = '/'
    port = 80 if scheme == "http" else 443

    if ":" in host:
        host, port = host.split(":", 1)
        port = int(port)

    s = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
    )
    s.connect((host, port))

    if scheme == "https":
        ctx = ssl.create_default_context()
        s = ctx.wrap_socket(s, server_hostname=host)

    s.send("GET {} HTTP/1.0\r\n".format(path).encode("utf8"))
    s.send(("Host: {}\r\n".format(host)).encode("utf8"))
    s.send(("Connection: close\r\n").encode("utf8"))
    s.send(("User-Agent: Mozilla/5.0 ({sys.platform})\r\n").encode("utf8"))
    s.send(("\r\n").encode("utf8"))
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    assert status in ("200", "301", "302"), "{}: {}".format(status, explanation)

    headers = {}
    while True:
        line = response.readline()
        if line == "\r\n":
            break
        header, value = line.split(":", 1)
        headers[header.lower()] = value.strip()

    global redirects_times
    if status in ("301", "302"):
        if redirects_times > 10:
            raise Exception("redirects times > 10 !")
        if not headers['location']:
            raise Exception("no headers.location")
        redirects_times = redirects_times + 1
        return request(headers["location"])
    else:
        redirects_times = 0

    body = response.read()
    s.close()

    return headers, body

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

def show(body):
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
        elif t.tag == "body":
            in_body = True
        elif t.tag == "/body":
            in_body = False
    print(body_text)

def load(url):
    headers, body = request(url)
    show(body)


if __name__ == "__main__":
    import sys
    load(sys.argv[1])
