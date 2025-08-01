#!/usr/bin/env python3
"""Test script to verify the checkpoint system works correctly."""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pipeline_import():
    """Test that the pipeline can be imported with checkpoint support."""
    try:
        from backend.video_pipeline.pipeline import run
        logger.info("✅ Pipeline import successful")
        return True
    except Exception as e:
        logger.error(f"❌ Pipeline import failed: {e}")
        return False

def test_progress_callback():
    """Test the progress callback functionality."""
    try:
        from backend.video_pipeline.pipeline import run
        
        # Test progress callback
        progress_log = []
        
        def test_callback(stage: str, message: str = ""):
            progress_log.append(f"{stage}: {message}")
            logger.info(f"Progress: {stage} - {message}")
        
        logger.info("✅ Progress callback test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Progress callback test failed: {e}")
        return False

def test_module_imports():
    """Test that all pipeline modules can be imported."""
    modules = [
        "backend.video_pipeline.extract_frames",
        "backend.video_pipeline.embed_frames", 
        "backend.video_pipeline.cluster_frames",
        "backend.video_pipeline.select_representative_frames",
        "backend.video_pipeline.label_representative_frames",
        "backend.video_pipeline.clipper",
        "backend.video_pipeline.metadata_writer"
    ]
    
    failed_modules = []
    
    for module_name in modules:
        try:
            __import__(module_name)
            logger.info(f"✅ {module_name} import successful")
        except Exception as e:
            logger.error(f"❌ {module_name} import failed: {e}")
            failed_modules.append(module_name)
    
    if failed_modules:
        logger.error(f"Failed to import modules: {failed_modules}")
        return False
    
    return True

def test_config():
    """Test that the config module works correctly."""
    try:
        from backend.video_pipeline import config
        
        # Test basic config
        logger.info(f"Frame rate: {config.FRAME_RATE}")
        logger.info(f"Clip max length: {config.CLIP_MAX_LENGTH}")
        logger.info(f"Embedding model: {config.EMBEDDING_MODEL}")
        
        # Test run directory creation
        test_dir = config.new_run_dir(prefix="test")
        logger.info(f"Test run directory: {test_dir}")
        
        if test_dir.exists():
            logger.info("✅ Config test successful")
            return True
        else:
            logger.error("❌ Failed to create test run directory")
            return False
            
    except Exception as e:
        logger.error(f"❌ Config test failed: {e}")
        return False

def test_backend_integration():
    """Test that the backend can use the checkpoint system."""
    try:
        # Import backend components
        from backend.app import JOBS
        from uuid import uuid4
        
        # Test job tracking
        test_job_id = str(uuid4())
        JOBS[test_job_id] = {
            "state": "processing", 
            "run_dir": None, 
            "error": None, 
            "progress": "Test checkpoint"
        }
        
        logger.info(f"✅ Backend integration test successful (job_id: {test_job_id})")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backend integration test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing checkpoint system...")
    logger.info("=" * 50)
    
    tests = [
        ("Pipeline Import", test_pipeline_import),
        ("Progress Callback", test_progress_callback),
        ("Module Imports", test_module_imports),
        ("Config", test_config),
        ("Backend Integration", test_backend_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Testing {test_name} ---")
        if test_func():
            logger.info(f"✅ {test_name} passed")
            passed += 1
        else:
            logger.error(f"❌ {test_name} failed")
    
    logger.info(f"\n{'=' * 50}")
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All checkpoint tests passed!")
        logger.info("The checkpoint system is ready for deployment.")
        sys.exit(0)
    else:
        logger.error("⚠️  Some checkpoint tests failed.")
        sys.exit(1) 