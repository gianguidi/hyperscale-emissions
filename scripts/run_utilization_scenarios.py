#!/usr/bin/env python
"""Backward-compatible wrapper for the Round 3 scenario workflow.

The old script name is retained because it appears in earlier README and review
materials. It now calls the total-output attribution workflow by default.
"""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("run_emissions_total_output.py")), run_name="__main__")
