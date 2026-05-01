
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = ROOT / "www" / "bootstrap.php"


class PhpSafeRenderingTest(unittest.TestCase):
    def test_e_and_ui_excerpt_do_not_convert_arrays_to_string(self):
        php = shutil.which("php")
        if not php:
            self.skipTest("php executable not available")

        source = BOOTSTRAP.read_text(encoding="utf-8")
        start = source.index("function mycelia_scalar_text")
        end = source.index("function redirect")
        functions = source[start:end]

        script = """<?php
declare(strict_types=1);
%s
$cases = [
    ['redacted' => 'true', 'text' => '[redacted:strict-vram]'],
    ['policy' => 'engine-context-escaped-html-text', 'text' => '&lt;safe&gt;'],
    ['a', 'b'],
    ['nested' => ['x' => 'y']],
    '<tag>',
];
foreach ($cases as $case) {
    echo e($case) . "\\n";
}
echo ui_excerpt(['redacted' => 'true', 'text' => 'Krümmel'], 20) . "\\n";
?>""" % functions

        with tempfile.TemporaryDirectory() as tmp:
            script_path = Path(tmp) / "render.php"
            script_path.write_text(script, encoding="utf-8")
            result = subprocess.run([php, str(script_path)], capture_output=True, text=True, check=False)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Array to string conversion", result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "[redacted:strict-vram]")
        self.assertEqual(lines[1], "&lt;safe&gt;")
        self.assertEqual(lines[2], "a, b")
        self.assertEqual(lines[3], "[structured-data]")
        self.assertEqual(lines[4], "&lt;tag&gt;")
        self.assertEqual(lines[5], "Krümmel")


    def test_layout_and_ownership_helpers_accept_structured_safe_fragments(self):
        source = BOOTSTRAP.read_text(encoding="utf-8")
        self.assertIn("function layout_header(mixed $title): void", source)
        self.assertNotIn("function layout_header(string $title): void", source)
        self.assertIn("function ownership_actions(mixed $ownerSignature, mixed $editUrl, mixed $deleteName, mixed $signature): string", source)
        self.assertIn("function mycelia_url_component(mixed $value): string", source)
        self.assertIn("function mycelia_identity(mixed $value): string", source)


if __name__ == "__main__":
    unittest.main()
