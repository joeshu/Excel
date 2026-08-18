import unittest
from pathlib import Path
from unittest.mock import patch

from app.routers.examples import list_tutorials


class ExamplesRouterTests(unittest.TestCase):
    def test_lists_medium_and_complex_tutorials(self):
        with patch("app.routers.examples.example_root", return_value=Path(__file__).parents[2] / "sample_data" / "scenarios"):
            result = list_tutorials()
        self.assertEqual({item["scenario"] for item in result["tutorials"]}, {"standard_formula", "multi_sheet_complex"})
        self.assertEqual({item["complexity"] for item in result["tutorials"]}, {"medium", "complex"})
        self.assertTrue(all(item["content"].startswith("#") for item in result["tutorials"]))


if __name__ == "__main__":
    unittest.main()
