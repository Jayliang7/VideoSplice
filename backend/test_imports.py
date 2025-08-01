#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly.
Run this from the backend directory.
"""

import sys
from pathlib import Path

# Add the parent directory to the Python path
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all the imports that were causing issues."""
    try:
        print("Testing imports...")
        
        # Test the main pipeline import
        from backend.video_pipeline.pipeline import run
        print("✓ pipeline import successful")
        
        # Test config import
        from backend.video_pipeline import config
        print("✓ config import successful")
        
        # Test other module imports
        from backend.video_pipeline.video_io import get_video_props
        print("✓ video_io import successful")
        
        from backend.video_pipeline.extract_frames import run as extract_frames
        print("✓ extract_frames import successful")
        
        from backend.video_pipeline.embed_frames import run as embed_frames
        print("✓ embed_frames import successful")
        
        from backend.video_pipeline.cluster_frames import run as cluster_frames
        print("✓ cluster_frames import successful")
        
        from backend.video_pipeline.select_representative_frames import run as choose_reps
        print("✓ select_representative_frames import successful")
        
        from backend.video_pipeline.label_representative_frames import run as label_reps
        print("✓ label_representative_frames import successful")
        
        from backend.video_pipeline.clipper import run as clipper
        print("✓ clipper import successful")
        
        from backend.video_pipeline.metadata_writer import write as write_meta
        print("✓ metadata_writer import successful")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports() 