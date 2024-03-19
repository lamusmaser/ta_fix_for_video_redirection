# TA Fix for Video Redirection
Fix videos in TA that are detected as associated to the YouTube Viewers channel, or another channel used when marked as "Video is Unavailable", as part of a video redirection response when pulling metadata.

This goes through and attempts to pull the following information:
Confirm that the actual file location and the ES file location match
Confirm that the video entry in ES is able to be updated through a TubeArchivist re-index
Determine if there is a need for thumbnail replacement


