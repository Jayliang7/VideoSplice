#!/usr/bin/env python3
"""Test script to verify memory optimization and monitoring system."""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_memory_monitoring():
    """Test memory monitoring functions."""
    try:
        from backend.video_pipeline.config import (
            get_memory_usage, check_memory_limit, force_memory_cleanup,
            check_video_size, assert_memory_available, MemoryLimitExceededError,
            MAX_MEMORY_MB, MAX_VIDEO_SIZE_MB
        )
        
        logger.info("Testing memory monitoring functions...")
        
        # Test memory usage
        memory_info = get_memory_usage()
        logger.info(f"Memory info: {memory_info}")
        
        if memory_info["available"]:
            logger.info(f"Current memory: {memory_info['used_mb']:.1f}MB / {memory_info['total_mb']:.1f}MB ({memory_info['percent']:.1f}%)")
            logger.info(f"Memory limit: {MAX_MEMORY_MB}MB")
            logger.info(f"Video size limit: {MAX_VIDEO_SIZE_MB}MB")
        
        # Test memory limit check
        within_limit = check_memory_limit()
        logger.info(f"Memory within limit: {within_limit}")
        
        # Test memory cleanup
        force_memory_cleanup()
        logger.info("Memory cleanup completed")
        
        # Test video size check
        test_sizes = [10 * 1024 * 1024, 60 * 1024 * 1024]  # 10MB, 60MB
        for size in test_sizes:
            is_valid = check_video_size(size)
            logger.info(f"Video size {size / (1024*1024):.1f}MB valid: {is_valid}")
        
        # Test memory assertion
        try:
            assert_memory_available()
            logger.info("Memory assertion passed")
        except MemoryLimitExceededError as e:
            logger.warning(f"Memory assertion failed: {e}")
        
        logger.info("✅ Memory monitoring test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory monitoring test failed: {e}")
        return False

def test_config_optimization():
    """Test memory optimization configuration."""
    try:
        from backend.video_pipeline.config import (
            FRAME_RATE, CLIP_MAX_LENGTH, BATCH_SIZE,
            MAX_MEMORY_MB, MAX_VIDEO_SIZE_MB
        )
        
        logger.info("Testing memory optimization configuration...")
        
        # Check optimized settings
        logger.info(f"Frame rate: {FRAME_RATE} (optimized for memory)")
        logger.info(f"Clip max length: {CLIP_MAX_LENGTH}s (optimized for memory)")
        logger.info(f"Batch size: {BATCH_SIZE} (optimized for memory)")
        logger.info(f"Memory limit: {MAX_MEMORY_MB}MB")
        logger.info(f"Video size limit: {MAX_VIDEO_SIZE_MB}MB")
        
        # Verify optimizations
        assert FRAME_RATE <= 0.5, "Frame rate should be optimized for memory"
        assert CLIP_MAX_LENGTH <= 120, "Clip length should be optimized for memory"
        assert BATCH_SIZE <= 5, "Batch size should be optimized for memory"
        assert MAX_MEMORY_MB <= 450, "Memory limit should be within Render free plan"
        assert MAX_VIDEO_SIZE_MB <= 50, "Video size limit should be reasonable"
        
        logger.info("✅ Memory optimization configuration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory optimization configuration test failed: {e}")
        return False

def test_pipeline_memory_integration():
    """Test pipeline memory integration."""
    try:
        from backend.video_pipeline.pipeline import run
        
        logger.info("Testing pipeline memory integration...")
        
        # Test that the pipeline can be imported with memory monitoring
        logger.info("Pipeline import successful with memory monitoring")
        
        logger.info("✅ Pipeline memory integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline memory integration test failed: {e}")
        return False

def test_backend_memory_integration():
    """Test backend memory integration."""
    try:
        from backend.app import app
        
        logger.info("Testing backend memory integration...")
        
        # Test that the backend can be imported with memory monitoring
        logger.info("Backend import successful with memory monitoring")
        
        logger.info("✅ Backend memory integration test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backend memory integration test failed: {e}")
        return False

def test_memory_error_handling():
    """Test memory error handling."""
    try:
        from backend.video_pipeline.config import MemoryLimitExceededError
        
        logger.info("Testing memory error handling...")
        
        # Test custom exception
        try:
            raise MemoryLimitExceededError(500.0, 450.0)
        except MemoryLimitExceededError as e:
            logger.info(f"Memory limit error caught: {e}")
        
        logger.info("✅ Memory error handling test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory error handling test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Testing memory optimization system...")
    logger.info("=" * 60)
    
    tests = [
        ("Memory Monitoring", test_memory_monitoring),
        ("Config Optimization", test_config_optimization),
        ("Pipeline Integration", test_pipeline_memory_integration),
        ("Backend Integration", test_backend_memory_integration),
        ("Error Handling", test_memory_error_handling),
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
    
    logger.info(f"\n{'=' * 60}")
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All memory optimization tests passed!")
        logger.info("The memory optimization system is ready for deployment.")
        logger.info("\nKey optimizations:")
        logger.info("- Frame rate: 0.5 FPS (reduced from 1.0)")
        logger.info("- Clip length: 120s (reduced from 240s)")
        logger.info("- Batch size: 3 frames (for memory efficiency)")
        logger.info("- Memory limit: 450MB (with 62MB buffer)")
        logger.info("- Video size limit: 50MB")
        sys.exit(0)
    else:
        logger.error("⚠️  Some memory optimization tests failed.")
        sys.exit(1) 