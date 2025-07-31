from video_pipeline.pipeline import run

video_path = "uploads/sample_video.mp4"  # must be relative to backend/
run_dir = run(video_path, prefix="test")

print(f"\n✅ Pipeline complete. Output saved to: {run_dir}")
