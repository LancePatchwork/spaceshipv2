# Hash Cache Usage Guide

## 🎯 **Automatic Hash Caching for ALL Tests**

**YES!** The hash cache system now works for **ALL pytest tests** automatically:

- ✅ **No decorators needed** - All tests get hash caching by default
- ✅ **Smart auto-detection** - Infers file dependencies from test names and locations
- ✅ **Override options** - Full control when you need it
- ✅ **Backward compatible** - Explicit decorators still work
- 🚨 **CRITICAL**: Only **PASSING** tests are cached - failed tests run every time until fixed

## 🚀 **Override Options for Hash-Based Test Caching**

The hash cache plugin provides several ways to override the caching behavior:

### **1. Force All Tests to Run**
```bash
# Run all tests regardless of file changes
pytest --force-hash-cache

# Run specific test file with force
pytest engine/tests/test_rule_compliance_optimized.py --force-hash-cache
```

### **2. Clear Cache and Run All Tests**
```bash
# Clear cache and run all tests (same as force, but also clears cache)
pytest --clear-hash-cache

# Clear cache and run specific tests
pytest engine/tests/ --clear-hash-cache
```

### **3. Invalidate Specific Files**
```bash
# Invalidate cache for specific files
pytest --invalidate-file engine/m02_events/models.py

# Invalidate multiple files
pytest --invalidate-file engine/m02_events/models.py --invalidate-file ui/core/registry.py

# Invalidate and run tests
pytest --invalidate-file engine/m02_events/models.py --force-hash-cache
```

### **4. Clear Cache Completely**
```bash
# Clear cache without running tests
pytest --clear-hash-cache --collect-only

# Or manually delete cache files
rm -rf .pytest_cache/hash_cache/
```

### **5. Disable Auto-Detection**
```bash
# Only use explicit decorators, disable auto-detection
pytest --no-auto-hash-cache

# Useful when you want full control over which tests use caching
```

## 📊 **Usage Scenarios**

### **Development Workflow**
```bash
# Normal development (fast, cached)
pytest

# After making changes to specific files
pytest --invalidate-file engine/m02_events/models.py

# When you want to be absolutely sure
pytest --force-hash-cache

# After major refactoring
pytest --clear-hash-cache
```

### **CI/CD Pipeline**
```bash
# Always run all tests in CI
pytest --force-hash-cache

# Or clear cache to ensure fresh start
pytest --clear-hash-cache
```

### **Debugging**
```bash
# Force run specific test that's being skipped
pytest engine/tests/test_rule_compliance_optimized.py::TestOptimizedRuleCompliance::test_no_print_statements_in_engine_code --force-hash-cache

# Check what files a test depends on
pytest --collect-only engine/tests/test_rule_compliance_optimized.py
```

## 🎯 **When to Use Each Option**

### **`--force-hash-cache`**
- ✅ When you want to run all tests regardless of changes
- ✅ In CI/CD pipelines
- ✅ When debugging test issues
- ✅ When you're unsure if cache is working correctly

### **`--clear-hash-cache`**
- ✅ After major refactoring
- ✅ When cache seems corrupted
- ✅ When you want a fresh start
- ✅ Before important releases

### **`--invalidate-file`**
- ✅ When you know specific files changed
- ✅ When you want to re-run tests for specific modules
- ✅ When debugging issues in specific files
- ✅ When you want targeted testing

### **`--no-auto-hash-cache`**
- ✅ When you want explicit control over caching
- ✅ When auto-detection is causing issues
- ✅ When you prefer manual decorator management
- ✅ For debugging the auto-detection system

## 🔧 **Advanced Usage**

### **Combining Options**
```bash
# Clear cache and force run
pytest --clear-hash-cache --force-hash-cache

# Invalidate specific files and force run
pytest --invalidate-file engine/m02_events/models.py --force-hash-cache

# Clear cache and run specific test
pytest --clear-hash-cache engine/tests/test_rule_compliance_optimized.py
```

### **Environment Variables**
```bash
# Set environment variable to always force
export PYTEST_FORCE_HASH_CACHE=1
pytest

# Or in your shell profile
echo 'export PYTEST_FORCE_HASH_CACHE=1' >> ~/.bashrc
```

### **Pytest Configuration**
```ini
# In pytest.ini
[tool:pytest]
addopts = --force-hash-cache  # Always force run
```

## 📈 **Performance Comparison**

| Command | Speed | Use Case |
|---------|-------|----------|
| `pytest` | ⚡ Fastest | Normal development |
| `pytest --invalidate-file file.py` | 🚀 Fast | Specific file changed |
| `pytest --force-hash-cache` | 🐌 Slow | Full scan needed |
| `pytest --clear-hash-cache` | 🐌 Slow | Fresh start needed |

## 🎯 **Best Practices**

1. **Normal Development**: Use `pytest` (cached)
2. **After File Changes**: Use `pytest --invalidate-file changed_file.py`
3. **CI/CD**: Use `pytest --force-hash-cache`
4. **Debugging**: Use `pytest --force-hash-cache` for specific tests
5. **Major Changes**: Use `pytest --clear-hash-cache`

## 🚨 **Troubleshooting**

### **Tests Skipping When They Shouldn't**
```bash
# Force run to check if tests actually work
pytest --force-hash-cache

# Clear cache if force run works
pytest --clear-hash-cache
```

### **Cache Corruption**
```bash
# Clear cache completely
rm -rf .pytest_cache/hash_cache/
pytest
```

### **Performance Issues**
```bash
# Check if cache is working
pytest --collect-only  # Should show skipped tests
pytest --force-hash-cache  # Should run all tests
```

## 🚨 **CRITICAL SAFETY FEATURES**

### **Failed Tests Are Never Cached**
- ❌ **Failed tests run every time** until they pass
- ✅ **Only passing tests get cached** for speed
- 🔄 **Failed tests invalidate their cache** automatically
- 🛡️ **Quality assurance**: Broken code can't hide behind cache

### **Why This Matters**
```bash
# First run: Test fails, not cached
pytest test_broken_code.py  # FAILED - not cached

# Fix the code, run again: Test passes, gets cached
pytest test_broken_code.py  # PASSED - now cached

# Subsequent runs: Test skipped (cached)
pytest test_broken_code.py  # SKIPPED - cached
```

This ensures that **broken code can never hide behind the cache** - failed tests will always run until they're fixed!
