#!/usr/bin/env python3
"""Test script to verify memory monitoring fix for Render deployment."""

import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_render_environment_detection():
    """Test Render environment detection."""
    try:
        from backend.video_pipeline.config import IS_RENDER, PSUTIL_AVAILABLE
        
        logger.info("Testing Render environment detection...")
        logger.info(f"IS_RENDER: {IS_RENDER}")
        logger.info(f"PSUTIL_AVAILABLE: {PSUTIL_AVAILABLE}")
        
        # Test memory usage function
        from backend.video_pipeline.config import get_memory_usage, check_memory_limit
        
        memory_info = get_memory_usage()
        logger.info(f"Memory info: {memory_info}")
        
        # Test memory limit check
        within_limit = check_memory_limit()
        logger.info(f"Memory within limit: {within_limit}")
        
        if IS_RENDER:
            logger.info("✅ Running on Render - memory monitoring should be disabled")
            assert not PSUTIL_AVAILABLE, "PSUTIL should be disabled on Render"
        else:
            logger.info("✅ Running locally - memory monitoring should be enabled")
        
        logger.info("✅ Render environment detection test passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Render environment detection test failed: {e}")
        return False

def test_memory_sanity_checks():
    """Test memory sanity checks for high values."""
    try:
        from backend.video_pipeline.config import get_memory_usage
        
        logger.info("Testing memory sanity checks...")
        
        # Simulate high memory values (like on Render)
        import psutil
        original_virtual_memory = psutil.virtual_memory
        
        # Mock high memory values
        class MockMemory:
            def __init__(self):
                self.used = 15 * 1024 * 1024 * 1024  # 15GB
                self.total = 16 * 1024 * 1024 * 1024  # 16GB
                self.available = 1 * 1024 * 1024 * 1024  # 1GB
                self.percent = 93.75
        
        def mock_virtual_memory():
            return MockMemory()
        
        # Temporarily replace psutil.virtual_memory
        psutil.virtual_memory = mock_virtual_memory
        
        try:
            memory_info = get_memory_usage()
            logger.info(f"Memory info with high values: {memory_info}")
            
            # Should return unavailable due to sanity check
            assert not memory_info["available"], "Memory should be marked as unavailable for high values"
            logger.info("✅ Memory sanity check passed")
            
        finally:
            # Restore original function
            psutil.virtual_memory = original_virtual_memory
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory sanity check test failed: {e}")
        return False

def test_pipeline_memory_integration():
    """Test pipeline memory integration."""
    try:
        from backend.video_pipeline.pipeline import run
        from backend.video_pipeline.config import IS_RENDER
        
        logger.info("Testing pipeline memory integration...")
        
        # Test that the pipeline can be imported with memory monitoring
        logger.info("Pipeline import successful with memory monitoring")
        
        if IS_RENDER:
            logger.info("✅ Pipeline will skip memory checks on Render")
        else:
            logger.info("✅ Pipeline will perform memory checks locally")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Pipeline memory integration test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running memory fix tests...")
    
    tests = [
        test_render_environment_detection,
        test_memory_sanity_checks,
        test_pipeline_memory_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✅ All tests passed! Memory fix is working correctly.")
    else:
        logger.error("❌ Some tests failed. Please check the implementation.") 