# TA Fix for Video Redirection
> [!NOTE]
> UNOFFICIAL HELPER SCRIPT

Fix videos in TA that are detected as associated to the YouTube Viewers channel, or another channel used when marked as "Video is Unavailable", as part of a video redirection response when pulling metadata.

This is usually indicated by videos having associations with the following channel(s) or video(s):
ID | Association Location | Type
:--- | :--- | ---:
UCMDQxm7cUx3yXkfeHa5zJIQ | `media_url` | Channel
M5t4UHllkUM | `vid_thumb_url` | Video


## Current functionality
This goes through and attempts to pull the following information:
- Confirm that the actual file location and the ES file location match
- Confirm that the video entry in ES is able to be updated through a TubeArchivist re-index
- Determine if there is a need for thumbnail replacement

This does not start a re-index or thumbnail update on TubeArchivist.


## Additional Arguments
> [!WARNING]
> Using this script is a destructive process and could cause issues with Elasticsearch. It is recommended to not use it unless advised or after you have reviewed an initial output of what is expected to happen.

Argument | Flag | Default | Purpose
:--- | :---: | :---: | :---
`SOURCE_DIR` | -d | `/youtube` | The source directory that will be searched for videos that need to be migrated. This can be used to specify an individual folder instead of the entire `/youtube` directory[^1].
`USE_YTDLP` | -Y | `False` | Allows the user to make calls to YouTube via `yt-dlp`. This will replace only making calls to ElasticSearch - this can add significant time to the overall process. 
`YTDLP_SLEEP` | -s | `3` | Number of seconds to wait between each call to YouTube when using `yt-dlp`. Value will not be used if `USE_YTDLP` is set to `False`.
`DEBUG` | -B | `False` | If set to `True`, this will show debugging outputs.
`DRY_RUN` | -D | `False` | If set to `True`, then it will only show what it expects to change. All details are preceeded with a `DRY_RUN` statement.

[^1]: This could cause issues with the ES updates portion, as it will be relative to the `SOURCE_DIR`.


## Running Script
This is expected to run from within the TubeArchivist container, at the `/app` directory. This allows it to see the TubeArchivist helper functions.

First, login to the TubeArchivist container. Instructions on how to do this are dependent on your platform. To download the script into the container, you can use `curl`. For example:
```
curl https://raw.githubusercontent.com/lamusmaser/ta_fix_for_video_redirection/main/ta_fix_for_redirection.py -o ta_fix_for_redirection.py
```
After the script is downloaded, you can run it with the following command:
```
python ta_fix_for_redirection.py
```

You can run this script with the optional flags. For example:
```
python ta_fix_for_redirection.py -Y -B -D
```

This would enable YouTube calls via `yt-dlp`, enable debugging outputs, but not perform any changes while outputting details as a dry run attempt.
