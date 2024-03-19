import argparse
import json
import mimetypes
import os
import re
import shutil
import stat
import string
import time

import yt_dlp
from home.src.es.connect import ElasticWrap, IndexPaginate

class FakeLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        pass

def parse_args():
    default_source = "/youtube"
    parser = argparse.ArgumentParser(description="TA Migration Helper Script")
    # Optional arguments
    parser.add_argument(
        '-d', '--SOURCE_DIR',
        default=default_source,
        help="The source directory that will be searched for videos that need to be migrated."
    )
    global args
    args = parser.parse_args()
    if args.DEBUG:
        dprint("Arguments provided:")
        for arg in vars(args):
            dprint(f"\t{arg}: {getattr(args, arg)}")

def dprint(value, **kwargs):
    if args.DEBUG:
        print(f"DEBUG:\t{value}", **kwargs)

def main():
    parse_args()
    print("Ending the redirected video fix process.")

if __name__ == "__main__":
    print("Starting script...")
    main()
    print("Script finished. Exiting.")