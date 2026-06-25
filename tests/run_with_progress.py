"""Run unittest tests with GitHub Actions-friendly progress logs."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class ProgressResult(unittest.TextTestResult):
    def __init__(self, *args, total_tests: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self.total_tests = total_tests
        self.current_test = 0

    def startTest(self, test):
        self.current_test += 1
        description = test.shortDescription() or str(test)
        print(f"::group::[{self.current_test}/{self.total_tests}] {description}", flush=True)
        print(f"Running {test.id()}", flush=True)
        super().startTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        print("Result: passed", flush=True)

    def addFailure(self, test, err):
        print("Result: failed", flush=True)
        super().addFailure(test, err)

    def addError(self, test, err):
        print("Result: error", flush=True)
        super().addError(test, err)

    def addSkip(self, test, reason):
        print(f"Result: skipped - {reason}", flush=True)
        super().addSkip(test, reason)

    def stopTest(self, test):
        super().stopTest(test)
        print("::endgroup::", flush=True)


class ProgressRunner(unittest.TextTestRunner):
    resultclass = ProgressResult

    def _makeResult(self):
        return self.resultclass(
            self.stream,
            self.descriptions,
            self.verbosity,
            total_tests=self.total_tests,
        )


def main() -> int:
    os.chdir(ROOT)
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    total_tests = suite.countTestCases()
    print(f"Discovered {total_tests} unit tests.", flush=True)

    runner = ProgressRunner(verbosity=2)
    runner.total_tests = total_tests
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
