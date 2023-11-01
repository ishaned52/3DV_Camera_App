from pymediainfo import MediaInfo

def get_video_details(file_path):
    media_info = MediaInfo.parse(file_path)

    for track in media_info.tracks:
        if track.track_type == 'Video':
            print(f"Video Codec: {track.codec}")
            print(f"Frame Rate: {track.frame_rate}")
            print(f"Resolution: {track.width}x{track.height}")
            print(f"Bitrate: {track.bit_rate} bps")
            print(f"Duration: {track.duration} seconds")
        elif track.track_type == 'Audio':
            print(f"Audio Codec: {track.codec}")
            print(f"Channels: {track.channel_s}")
            print(f"Sample Rate: {track.sampling_rate} Hz")
            print(f"Bitrate: {track.bit_rate} bps")
            print(f"Duration: {track.duration} seconds")

if __name__ == "__main__":
    # Replace 'your_video_path.mp4' with the actual path to your video file
    # video_path = '/media/giocam3d/GIOVIEW/Recordings/UHD_150556.mp4'

    video_path = '/media/giocam3d/GIOVIEW/venom.mp4'
    # /media/giocam3d/GIOVIEW/Other/venom.mp4
    
    get_video_details(video_path)
