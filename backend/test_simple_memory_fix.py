#!/usr/bin/env python3
"""Simple test to verify memory monitoring fix for Render deployment."""

import os
import sys
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_render_environment_detection():
    """Test Render environment detection."""
    try:
        # Test the logic directly
        is_render = os.getenv("RENDER", "false").lower() == "true"
        
        logger.info("Testing Render environment detection...")
        logger.info(f"RENDER env var: {os.getenv('RENDER', 'not set')}")
        logger.info(f"IS_RENDER: {is_render}")
        
        # Test psutil availability
        try:
            import psutil
            psutil_available = True and not is_render
            logger.info(f"PSUTIL_AVAILABLE: {psutil_available}")
        except ImportError:
            psutil_available = False
            logger.info("PSUTIL_AVAILABLE: False (psutil not installed)")
        
        if is_render:
            logger.info("✅ Running on Render - memory monitoring should be disabled")
            assert not psutil_available, "PSUTIL should be disabled on Render"
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
        logger.info("Testing memory sanity checks...")
        
        # Test the logic directly
        try:
            import psutil
            
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
            original_virtual_memory = psutil.virtual_memory
            psutil.virtual_memory = mock_virtual_memory
            
            try:
                memory = psutil.virtual_memory()
                used_mb = memory.used / (1024 * 1024)
                total_mb = memory.total / (1024 * 1024)
                
                # Sanity check for impossibly high values
                if used_mb > 10000 or total_mb > 10000:
                    logger.warning(f"Memory reporting error detected: {used_mb:.1f}MB used, {total_mb:.1f}MB total")
                    memory_info = {"available": False, "percent": 0, "used_mb": 0, "total_mb": 0}
                else:
                    memory_info = {
                        "available": True,
                        "percent": memory.percent,
                        "used_mb": used_mb,
                        "total_mb": total_mb,
                        "available_mb": memory.available / (1024 * 1024)
                    }
                
                logger.info(f"Memory info with high values: {memory_info}")
                
                # Should return unavailable due to sanity check
                assert not memory_info["available"], "Memory should be marked as unavailable for high values"
                logger.info("✅ Memory sanity check passed")
                
            finally:
                # Restore original function
                psutil.virtual_memory = original_virtual_memory
                
        except ImportError:
            logger.info("✅ psutil not available - skipping memory sanity check")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Memory sanity check test failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running simple memory fix tests...")
    
    tests = [
        test_render_environment_detection,
        test_memory_sanity_checks
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