"""Check the user-visible log/exit contract with real child processes."""
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lab_ux import run_step


class ProgressTest(unittest.TestCase):
    def run_child(self, code, verbose=False):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = run_step(4, 'Verify traffic', [sys.executable, '-c', code], verbose)
        return status, output.getvalue()

    def test_success_hides_technical_logs_and_reports_completion(self):
        status, output = self.run_child('print("technical-child-log")')
        self.assertEqual(status, 0)
        self.assertIn('[4/5] Verify traffic', output)
        self.assertIn('PASS', output)
        self.assertNotIn('technical-child-log', output)

    def test_failure_preserves_exit_code_and_bounds_diagnostics(self):
        status, output = self.run_child('import sys; print("old-log"); '
                                        '[print("detail") for _ in range(50)]; '
                                        'sys.stdout.flush(); print("actual-cause", file=sys.stderr); sys.exit(7)')
        self.assertEqual(status, 7)
        self.assertIn('FAIL [4/5]', output)
        self.assertIn('exit 7', output)
        self.assertIn('actual-cause', output)
        self.assertNotIn('old-log', output)
        self.assertIn('ARGS=--verbose', output)

    def test_plain_make_is_help_without_side_effects(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['make', '-n'], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('CLI-HELP.txt', result.stdout)
        self.assertNotIn('cp .env', result.stdout)
        self.assertNotIn('docker', result.stdout)
