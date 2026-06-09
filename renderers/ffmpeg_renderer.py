import os
import subprocess
from core.models import Timeline

class FFmpegRenderer:
    def __init__(self, fps: int = 1):
        self.fps = fps

    def render(self, timeline: Timeline, output_path: str):
        if not timeline.clips:
            raise ValueError("Timeline is empty")

        abs_output_path = os.path.abspath(output_path)
        temp_dir = os.path.dirname(abs_output_path) or "."
        os.makedirs(temp_dir, exist_ok=True)
        clip_paths = []

        print(f"Rendering {len(timeline.clips)} clips with audio...")

        for i, clip in enumerate(timeline.clips):
            clip_output = os.path.join(temp_dir, f"temp_clip_{i:04d}.mp4")
            clip_paths.append(clip_output)
            
            duration = max(1.0, clip.end_time - clip.start_time)
            
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", clip.image_path,
                "-ss", str(clip.audio_start_offset),  # Start audio at calculated offset
                "-i", clip.audio_path,                # Use the REAL generated audio file!
                "-c:v", "libx264",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2",
                "-t", str(duration),
                "-r", str(self.fps),
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",                        # Encode audio to AAC for MP4 compatibility
                "-shortest",
                clip_output
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"\n❌ FFmpeg failed on clip {i} (Page {clip.page_number})")
                print(f"FFmpeg Error Output:\n{result.stderr}")
                raise RuntimeError("FFmpeg rendering failed.")
            
            if (i + 1) % 50 == 0 or (i + 1) == len(timeline.clips):
                print(f"  Progress: {i + 1}/{len(timeline.clips)} clips rendered.")

        # Concatenate all clips
        print("Running final FFmpeg concatenation...")
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            for path in clip_paths:
                f.write(f"file '{path.replace(chr(92), '/')}'\n") # Force forward slashes

        final_cmd = [
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", concat_file, "-c", "copy", abs_output_path
        ]
        
        result = subprocess.run(final_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"\n❌ FFmpeg concatenation failed.\n{result.stderr}")
            raise RuntimeError("FFmpeg concatenation failed.")

        # Cleanup
        print("Cleaning up temporary clip files...")
        for path in clip_paths:
            if os.path.exists(path): os.remove(path)
        if os.path.exists(concat_file): os.remove(concat_file)
            
        print(f"✅ Successfully rendered: {abs_output_path}")