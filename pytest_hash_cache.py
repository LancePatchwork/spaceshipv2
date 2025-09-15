"""Pytest plugin for hash-based test caching.

This plugin allows tests to skip themselves if the files they depend on
haven't changed since the last run, based on file content hashes.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

import pytest


class HashCache:
    """Manages hash-based caching for test files."""

    def __init__(self, cache_dir: Path = Path(".pytest_cache/hash_cache")):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "file_hashes.json"
        self.test_cache_file = self.cache_dir / "test_hashes.json"

        # Load existing caches
        self.file_hashes = self._load_cache(self.cache_file)
        self.test_hashes = self._load_cache(self.test_cache_file)

    def _load_cache(self, cache_file: Path) -> Dict[str, Any]:
        """Load cache from file."""
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    return json.load(f)  # type: ignore[no-any-return]
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_cache(self, cache_file: Path, data: Dict[str, Any]) -> None:
        """Save cache to file."""
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass  # Fail silently if we can't write cache

    def get_file_hash(self, file_path: Path) -> str:
        """Get hash of file content."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except (IOError, OSError):
            return ""

    def get_files_hash(self, file_paths: List[Path]) -> str:
        """Get combined hash of multiple files."""
        hashes = []
        for file_path in file_paths:
            file_hash = self.get_file_hash(file_path)
            if file_hash:
                hashes.append(f"{file_path}:{file_hash}")

        combined = "|".join(sorted(hashes))
        return hashlib.sha256(combined.encode()).hexdigest()

    def has_files_changed(self, file_paths: List[Path]) -> bool:
        """Check if any of the specified files have changed."""
        current_hash = self.get_files_hash(file_paths)

        # Create a key for this set of files
        file_key = "|".join(sorted(str(p) for p in file_paths))

        # Check if hash has changed
        if file_key in self.file_hashes:
            return self.file_hashes[file_key] != current_hash  # type: ignore[no-any-return]

        # New files, consider them changed
        return True  # type: ignore[no-any-return]

    def update_file_cache(self, file_paths: List[Path]) -> None:
        """Update cache with current file hashes."""
        current_hash = self.get_files_hash(file_paths)
        file_key = "|".join(sorted(str(p) for p in file_paths))
        self.file_hashes[file_key] = current_hash
        self._save_cache(self.cache_file, self.file_hashes)

    def should_skip_test(self, test_name: str, file_paths: List[Path]) -> bool:
        """Check if test should be skipped based on file changes."""
        if self.has_files_changed(file_paths):
            return False  # Files changed, don't skip

        # Check if test itself has changed
        test_hash = self.get_test_hash(test_name)
        if test_name in self.test_hashes:
            return self.test_hashes[test_name] == test_hash  # type: ignore[no-any-return]

        return False  # New test, don't skip

    def get_test_hash(self, test_name: str) -> str:
        """Get hash of test function content."""
        # This would need to be implemented to get the actual test function
        # For now, we'll use a placeholder
        return hashlib.sha256(test_name.encode()).hexdigest()

    def update_test_cache(self, test_name: str, file_paths: List[Path]) -> None:
        """Update cache for a test."""
        test_hash = self.get_test_hash(test_name)
        self.test_hashes[test_name] = test_hash
        self._save_cache(self.test_cache_file, self.test_hashes)

        # Also update file cache
        self.update_file_cache(file_paths)

    def clear_cache(self) -> None:
        """Clear all cached hashes."""
        self.file_hashes.clear()
        self.test_hashes.clear()
        self._save_cache(self.cache_file, self.file_hashes)
        self._save_cache(self.test_cache_file, self.test_hashes)

    def invalidate_file(self, file_path: Path) -> None:
        """Invalidate cache for a specific file."""
        # Remove any cache entries that include this file
        keys_to_remove = []
        for key in self.file_hashes:
            if str(file_path) in key:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.file_hashes[key]

        self._save_cache(self.cache_file, self.file_hashes)

    def invalidate_test(self, test_name: str) -> None:
        """Invalidate cache for a specific test."""
        if test_name in self.test_hashes:
            del self.test_hashes[test_name]
            self._save_cache(self.test_cache_file, self.test_hashes)


# Global cache instance
_hash_cache = HashCache()

# Track test outcomes
_test_outcomes = {}


def _infer_test_dependencies(item) -> List[Path]:
    """Infer file dependencies for a test based on its name and location."""
    dependencies: List[Path] = []

    # Get the test file path
    test_file = Path(item.fspath)

    # For rule compliance tests, they typically scan entire directories
    if "rule_compliance" in str(test_file):
        if "engine" in str(test_file):
            dependencies.extend(Path("engine/").glob("**/*.py"))
        elif "ui" in str(test_file):
            dependencies.extend(Path("ui/").glob("**/*.py"))
        return dependencies

    # For architectural compliance tests
    if "architectural_compliance" in str(test_file):
        dependencies.extend(Path("engine/").glob("**/*.py"))
        dependencies.extend(Path("ui/").glob("**/*.py"))
        return dependencies

    # For module-specific tests, infer from test file location
    if "test_m01_" in str(test_file):
        dependencies.extend(Path("engine/m01_srs/").glob("**/*.py"))
    elif "test_m02_" in str(test_file):
        dependencies.extend(Path("engine/m02_events/").glob("**/*.py"))
    elif "test_m03_" in str(test_file):
        dependencies.extend(Path("engine/m03_geometry/").glob("**/*.py"))
    # Add more module patterns as needed

    # For UI tests
    if "ui/tests/" in str(test_file):
        # UI tests typically depend on the specific UI module being tested
        test_name = test_file.stem
        if "test_app" in test_name:
            dependencies.append(Path("ui/core/app.py"))
        elif "test_registry" in test_name:
            dependencies.append(Path("ui/core/registry.py"))
        elif "test_main_window" in test_name:
            dependencies.append(Path("ui/windows/main_window.py"))
        # Add more UI test patterns as needed

    # If no specific dependencies found, depend on the test file itself
    if not dependencies:
        dependencies.append(test_file)

    return dependencies


def pytest_addoption(parser):
    """Add command line options for hash cache plugin."""
    parser.addoption(
        "--force-hash-cache",
        action="store_true",
        default=False,
        help="Force all hash-cached tests to run even if files unchanged",
    )
    parser.addoption(
        "--clear-hash-cache",
        action="store_true",
        default=False,
        help="Clear hash cache and run all tests",
    )
    parser.addoption(
        "--invalidate-file",
        action="append",
        default=[],
        help="Invalidate cache for specific file (can be used multiple times)",
    )
    parser.addoption(
        "--no-auto-hash-cache",
        action="store_true",
        default=False,
        help="Disable automatic hash cache detection (only use explicit decorators)",
    )


def pytest_configure(config):
    """Configure pytest with hash cache plugin."""
    config.addinivalue_line("markers", "hash_cache: mark test to use hash-based caching")

    # Handle cache clearing
    if config.getoption("--clear-hash-cache"):
        _hash_cache.clear_cache()
        print("🗑️  Hash cache cleared - all tests will run")

    # Handle file invalidation
    invalidate_files = config.getoption("--invalidate-file")
    for file_path in invalidate_files:
        _hash_cache.invalidate_file(Path(file_path))
        print(f"🔄 Cache invalidated for: {file_path}")


def pytest_collection_modifyitems(config, items):
    """Modify test items to add hash cache markers."""
    for item in items:
        # Add hash_cache marker to all tests by default
        if not item.get_closest_marker("hash_cache"):
            item.add_marker(pytest.mark.hash_cache)

        # Auto-detect file dependencies for tests that don't have explicit decorators
        if not hasattr(item.function, "_hash_cache_files") and not config.getoption(
            "--no-auto-hash-cache"
        ):
            # Try to infer file dependencies from test name and location
            test_file_deps = _infer_test_dependencies(item)
            if test_file_deps:
                item.function._hash_cache_files = test_file_deps


def pytest_runtest_setup(item):
    """Setup test with hash cache checking."""
    if not item.get_closest_marker("hash_cache"):
        return

    # Check if force flag is set
    config = item.session.config
    force_run = config.getoption("--force-hash-cache", default=False)
    if force_run:
        return  # Skip cache checking, run all tests

    # Get files this test depends on
    file_paths = getattr(item.function, "_hash_cache_files", [])
    if not file_paths:
        return  # No files to check

    # Check if test should be skipped
    test_name = f"{item.module.__name__}::{item.name}"
    if _hash_cache.should_skip_test(test_name, file_paths):
        pytest.skip(f"Files unchanged since last run: {[str(p) for p in file_paths]}")


def pytest_runtest_logreport(report):
    """Track test outcomes for cache management."""
    if report.when == "call":  # Only track the actual test execution
        # Convert nodeid to the same format used in teardown
        # nodeid format: "path/to/file.py::Class::test_method"
        # teardown format: "module_name::test_name"
        parts = report.nodeid.split("::")
        if len(parts) >= 2:
            module_name = parts[0].replace("/", ".").replace("\\", ".").replace(".py", "")
            test_name = parts[-1]  # Last part is the test method name
            formatted_name = f"{module_name}::{test_name}"
        else:
            formatted_name = report.nodeid
        _test_outcomes[formatted_name] = report.outcome


def pytest_runtest_teardown(item):
    """Update cache after test runs - ONLY if test passed."""
    if not item.get_closest_marker("hash_cache"):
        return

    file_paths = getattr(item.function, "_hash_cache_files", [])
    if not file_paths:
        return

    test_name = f"{item.module.__name__}::{item.name}"

    # Only update cache if test passed
    if _test_outcomes.get(test_name) == "passed":
        _hash_cache.update_test_cache(test_name, file_paths)
        print(f"✅ Cached test: {test_name}")
    else:
        # If test failed, invalidate any existing cache for this test
        _hash_cache.invalidate_test(test_name)
        print(
            f"❌ Not caching failed test: {test_name} "
            f"(outcome: {_test_outcomes.get(test_name, 'unknown')})"
        )
    # If test failed, we don't update the cache - it will run again next time


def hash_cache_files(*file_paths: str):
    """Decorator to specify which files a test depends on."""

    def decorator(func):
        # Convert string paths to Path objects
        paths = [Path(p) for p in file_paths]
        func._hash_cache_files = paths
        return func

    return decorator


def hash_cache_glob(pattern: str, base_dir: str = "."):
    """Decorator to specify files using glob pattern."""

    def decorator(func):
        base_path = Path(base_dir)
        paths = list(base_path.glob(pattern))
        func._hash_cache_files = paths
        return func

    return decorator
