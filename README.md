# TA Fix for Video Redirection
Fix videos in TA that are detected as associated to the YouTube Viewers channel, or another channel used when marked as "Video is Unavailable", as part of a video redirection response when pulling metadata.

This goes through and attempts to pull the following information:
Confirm that the actual file location and the ES file location match
Confirm that the video entry in ES is able to be updated through a TubeArchivist re-index
Determine if there is a need for thumbnail replacement

## Running Script
This is expected to run from within the TubeArchivist container, at the `/app` directory. This allows it to see the TubeArchivist helper functions.

You can run this script with the optional flags. For example:
```
python ta_fix_for_redirections.py
```