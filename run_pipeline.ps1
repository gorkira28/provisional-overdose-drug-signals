$ErrorActionPreference = "Stop"
python python/acquire_and_analyze.py
python tests/test_outputs.py
