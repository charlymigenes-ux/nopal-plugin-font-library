import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PluginContractTests(unittest.TestCase):
    def test_manifest_matches_nopal_contract(self):
        manifest = json.loads((ROOT / "nopal-plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema_version"], 1)
        self.assertEqual(manifest["id"], "font-library")
        self.assertEqual(manifest["version"], "0.4.1")
        self.assertEqual(manifest["frontend"]["section"], "font-library")
        self.assertTrue((ROOT / manifest["frontend"]["script"]).is_file())
        self.assertTrue((ROOT / manifest["frontend"]["style"]).is_file())

    def test_frontend_registers_lifecycle(self):
        script = (ROOT / "frontend" / "font-library.js").read_text(encoding="utf-8")
        self.assertIn("NopalPluginRegistry", script)
        self.assertIn("function mount()", script)
        self.assertIn("function unmount()", script)
        for language in ("es", "en", "de", "fr", "pt-BR"):
            self.assertTrue(
                f"{language}:" in script or f"'{language}':" in script,
                f"Missing translation dictionary for {language}",
            )

    def test_javascript_syntax(self):
        result = subprocess.run(
            ["node", "--check", str(ROOT / "frontend" / "font-library.js")],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_workshop_flow_returns_editable_element_to_project(self):
        script = (ROOT / "frontend" / "font-library.js").read_text(encoding="utf-8")
        self.assertIn("function addToProject()", script)
        self.assertIn("nopal:add-project-element", script)
        self.assertIn("type: 'svg-text'", script)
        self.assertIn("dimensions: { widthMm", script)
        self.assertIn("editable: model.editable", script)
        self.assertIn("kerfMm", script)
        self.assertIn("function bindCanvasInteractions()", script)
        self.assertIn("addEventListener('pointermove'", script)
        self.assertIn("addEventListener('wheel'", script)
        self.assertIn("transform: { xMm:", script)
        for corner in ("nw", "ne", "sw", "se"):
            self.assertIn(f'data-fl-resize="{corner}"', script)
        self.assertIn("function warpPathToArc", script)
        self.assertIn("data-fl-curve", script)
        self.assertIn("event.key === 'Control'", script)
        self.assertIn("outlineMm", script)
        self.assertIn("outlineStyle", script)
        self.assertIn('data-fl-outline-style="solid"', script)
        self.assertIn('data-fl-outline-style="line"', script)


if __name__ == "__main__":
    unittest.main()
