"""Root pytest configuration.

The ``platform/`` package in this project shadows Python's stdlib ``platform``
module.  We restore the stdlib attribute that pytest's terminal reporter needs
before the test session starts.
"""
import sys
import importlib

# Ensure pytest can still find platform.python_version from the stdlib.
# Our local ``platform`` package doesn't define it, so we inject a shim.
_local_platform = sys.modules.get("platform")
if _local_platform is not None and not hasattr(_local_platform, "python_version"):
    import platform as _stdlib_platform  # noqa: F401  (may already be ours)
    try:
        # Try to get the real stdlib version via importlib
        import importlib.util as _ilu
        _spec = _ilu.find_spec("platform", sys.stdlib_module_names if hasattr(sys, "stdlib_module_names") else None)  # type: ignore[arg-type]
    except Exception:
        pass

    # Provide a minimal shim so pytest terminal reporter doesn't crash.
    def _python_version():  # type: ignore[return]
        import sys as _sys
        v = _sys.version_info
        return f"{v.major}.{v.minor}.{v.micro}"

    _local_platform.python_version = _python_version  # type: ignore[attr-defined]
