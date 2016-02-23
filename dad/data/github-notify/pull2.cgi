#!/usr/bin/python3

import os
import sys
import json

data = sys.stdin.read(int(os.environ.get('HTTP_CONTENT_LENGTH', 0)))

print("Content-type: text/plain\n\n")

print("got " + os.environ.get('HTTP_CONTENT_LENGTH', 0) + " bytes\n")

if data:
	print(list(json.loads(data).keys()))
else:
	print("no data!\n")

