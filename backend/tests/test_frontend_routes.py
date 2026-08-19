import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException

from app.main import frontend, frontend_asset


class FrontendRouteTests(unittest.TestCase):
    def test_frontend_returns_index_and_existing_asset(self):
        with tempfile.TemporaryDirectory() as directory:
            frontend_dist = Path(directory)
            (frontend_dist / "assets").mkdir()
            (frontend_dist / "index.html").write_text('<script type="module" src="/app/assets/index-abc.js"></script>', encoding="utf-8")
            asset = frontend_dist / "assets" / "index-abc.js"
            asset.write_text("console.log('ok');", encoding="utf-8")

            with patch("app.main.frontend_dist", frontend_dist):
                index_response = frontend()
                asset_response = frontend_asset("index-abc.js")

            self.assertEqual(Path(index_response.path), frontend_dist / "index.html")
            self.assertEqual(Path(asset_response.path), asset)

    def test_missing_asset_returns_not_found_instead_of_html(self):
        with tempfile.TemporaryDirectory() as directory:
            frontend_dist = Path(directory)
            (frontend_dist / "assets").mkdir()

            with patch("app.main.frontend_dist", frontend_dist):
                with self.assertRaises(HTTPException) as context:
                    frontend_asset("missing.js")

            self.assertEqual(context.exception.status_code, 404)
            self.assertIn("missing.js", context.exception.detail)


if __name__ == "__main__":
    unittest.main()
