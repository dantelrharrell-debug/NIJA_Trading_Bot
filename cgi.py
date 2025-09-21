# cgi.py - shim for Python 3.13 removal
import urllib.parse as _urlparse

def parse_header(line):
    parts = line.split(";")
    key = parts[0].strip().lower()
    pdict = {}
    for item in parts[1:]:
        if "=" in item:
            k, v = item.strip().split("=", 1)
            pdict[k.lower()] = v.strip()
    return key, pdict
