"""Run the built, integrated workstation under a local preview runner."""
import argparse

import uvicorn

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=8000)
parser.add_argument("--strictPort", action="store_true")
options = parser.parse_args()
uvicorn.run("app.main:app", host=options.host, port=options.port)
