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
    default_use_ytdlp = False
    default_ytdlp_sleep = 3
    default_dry_run = False
    default_debug = False
    parser = argparse.ArgumentParser(description="TA Migration Helper Script")
    # Optional arguments
    parser.add_argument(
        '-d', '--SOURCE_DIR',
        default=default_source,
        help="The source directory that will be searched for videos that need to be migrated."
    )
    parser.add_argument(
        '-Y', '--USE_YTDLP',
        default=default_use_ytdlp,
        action='store_true',
        help="Disable calls to YouTube via yt-dlp. If set, it will only search ElasticSearch."
    )
    parser.add_argument(
        '-s', '--YTDLP_SLEEP',
        type=int,
        default=default_ytdlp_sleep,
        help="Number of seconds to wait between each call to YouTube when using yt-dlp. This value is not used if USE_YTDLP is set to False."
    )
    parser.add_argument(
        '-D', '--DRY_RUN',
        default=default_dry_run,
        action='store_true',
        help="If set to True, this will attempt to change values in Elasticsearch. If False, it will perform a review of what changes need to occur and why."
    )
    parser.add_argument(
        '-B', '--DEBUG',
        default=default_debug,
        action='store_true',
        help="If set to True, this will show debugging outputs."
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


def review_filesystem(s_dir):
    # Walk through the /youtube directory
    print("Calculating number of files to process...")
    file_count = sum(len(files) for _, _, files in os.walk(s_dir))
    dprint(f"Total files found: {file_count}")
    video_files = {}
    all_files = []
    current_count = 0
    vid_types = [".mp4"]
    vid_id_length = 11

    print("Processing video files...")
    for root, _, files in os.walk(s_dir):
        for filename in files:
            current_count += 1
            all_files.append(os.path.join(root,filename))
            basename, ext = os.path.splitext(os.path.basename(filename))
            if ext in vid_types:
                if len(basename) == vid_id_length:
                    video_id = basename
                else:
                    break
                print(f"[{current_count}/{file_count}] Matching file: {filename} | Extracted Video ID: {video_id}")
                if video_id:
                    original_location = os.path.join(root, filename)
                    if video_files.get(video_id):
                        channel_id = video_files[video_id][0]['channel_id']
                    elif os.path.exists(os.path.join(root,"channel.id")):
                        with open(os.path.join(root,"channel.id"), 'r') as channel_file:
                            for line in channel_file.readlines():
                                if len(line) > 0:
                                    channel_id = line.strip()
                    else:
                        channel_id = get_channel_id(video_id)
                    if channel_id:
                        expected_location = os.path.join(os.path.join(s_dir, channel_id),f"{video_id}{os.path.splitext(filename)[-1]}")
                        if not video_files.get(video_id):
                            video_files[video_id] = []
                        det = {'channel_id': channel_id, 'type': "video", 'original_location': original_location, 'expected_location': expected_location}
                        video_files[video_id].append(det)
                    else:
                        print(f"Could not extract channel ID for `{filename}`.")
                else:
                    print(f"Could not extract video ID for `{filename}`.")
    dprint(f"All video files: {video_files}.")
    # dprint(f"All files in filesystem: {all_files}")
    return video_files, all_files


def get_channel_id(video_id):
    if args.USE_YTDLP:
        ydl_opts = {'quiet': True, 'logger': FakeLogger()}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                time.sleep(args.YTDLP_SLEEP)
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                dprint(f"Channel extracted from YTDL: {info.get('channel_id')}")
                return info.get('channel_id')
            except yt_dlp.utils.DownloadError as e:
                try:
                    return check_channel_id_from_es(video_id)
                except:
                    print(f"Failed to find video ID from YouTube or ElasticSearch for {video_id}. YouTube download error: {e}")
                    return None
    else:
        try:
            es_channel_id = check_channel_id_from_es(video_id)
            if es_channel_id:
                return es_channel_id
            return None 
        except:
            e = "USE_YTDLP set to False. YouTube Download Error does not exist."
            print(f"Failed to find video ID from YouTube or ElasticSearch for {video_id}. YouTube download error: {e}")
            return None


def check_channel_id_from_es(video_id):
    res = ElasticWrap("ta_video/_search").get(data={"query": {"match":{"_id": video_id}}})
    if res[1] == 200:
        res = res[0]
    channel_id = None
    for hit in res['hits']['hits']:
        channel_id = hit['_source']['channel']['channel_id']
    return channel_id


def pull_video_from_es(video_id):
    res = ElasticWrap("ta_video/_search").get(data={"query": {"match":{"_id": video_id}}})
    if res[1] == 200:
        res = res[0]
    video_ids = {}
    for hit in res['hits']['hits']:
        video_ids[hit['_id']] = {}
        video_ids[hit['_id']]['channel_id'] = hit['_source']['channel']['channel_id']
        video_ids[hit['_id']]['media_url'] = hit['_source']['media_url']
        video_ids[hit['_id']]['tags'] = hit['_source']['tags']
        video_ids[hit['_id']]['vid_last_refresh'] = hit['_source']['vid_last_refresh']
        video_ids[hit['_id']]['vid_thumb_base64'] = hit['_source']['vid_thumb_base64']
        video_ids[hit['_id']]['vid_thumb_url'] = hit['_source']['vid_thumb_url']
    return video_ids


def process_videos(video_files):
    for video in video_files.keys():
        videos_es = pull_video_from_es(video)
        for video_es in videos_es:
            expected_changes = {}
            if videos_es[video_es]['media_url'] not in video_files[video][0]["expected_location"]:
                expected_changes['media_url'] = video_files[video][0]["expected_location"].split(f"{args.SOURCE_DIR}/")[1]
            if video not in videos_es[video_es]['vid_thumb_url']:
                expected_changes['vid_thumb_url'] = videos_es[video_es]['vid_thumb_url'].replace(videos_es[video_es]['vid_thumb_url'].split("/")[-2],video)
            if expected_changes:
                expected_changes['vid_last_refresh'] = 1
                expected_changes['vid_thumb_base64'] = False
                expected_changes['tags'] = []
                if args.DRY_RUN:
                    for key in expected_changes.keys():
                        print(f"DRY_RUN:\tChanging Elasticsearch reference for Video ID {video}[{key}] - {videos_es[video_es][key]} -> {expected_changes[key]}.")
                else:
                    source = {}
                    source["doc"] = expected_changes
                    res = ElasticWrap(f"ta_video/_update/{video}").post(data = source)
                    try:
                        if res[1] == 200 and res[0]['_shards']['total'] == res[0]['_shards']['successful']:
                            print(f"ElasticSearch was updated successfully for ID {video}.")
                        else:
                            print(f"ElasticSearch was not updated successfully for ID {video}.")
                    except Exception as e:
                        print(f"Exception occurred during update of ElasticSearch for ID {video}: {e}")


def main():
    parse_args()
    source_dir = args.SOURCE_DIR
    if not os.path.exists(source_dir):
        print(f"The directory `{source_dir}` does not exist. Exiting.")
        return 1
    video_files, _ = review_filesystem(source_dir)
    process_videos(video_files)
    print("Ending the redirected video fix process.")

if __name__ == "__main__":
    print("Starting script...")
    main()
    print("Script finished. Exiting.")