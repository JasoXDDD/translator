"""Run unittest tests with GitHub Actions-friendly progress logs."""
from __future__ import annotations

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
        self.current_description = ""
        self.current_status = "finished"

    def startTest(self, test):
        self.current_test += 1
        self.current_description = test.shortDescription() or str(test)
        self.current_status = "finished"
        print(f"::group::[{self.current_test}/{self.total_tests}] {self.current_description}", flush=True)
        print(f"Running {test.id()}", flush=True)
        super().startTest(test)

    def addSuccess(self, test):
        self.current_status = "passed"
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.current_status = "failed"
        super().addFailure(test, err)

    def addError(self, test, err):
        self.current_status = "error"
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.current_status = f"skipped - {reason}"
        super().addSkip(test, reason)

    def stopTest(self, test):
        super().stopTest(test)
        print(
            f"Finished [{self.current_test}/{self.total_tests}] {self.current_description}: {self.current_status}",
            flush=True,
        )
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
    suite = unittest.defaultTestLoader.discover("tests", pattern="test_*.py")
    total_tests = suite.countTestCases()
    print(f"Discovered {total_tests} unit tests.", flush=True)

    runner = ProgressRunner(stream=sys.stdout, verbosity=2)
    runner.total_tests = total_tests
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
