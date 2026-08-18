import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

from app.services.batch_package import build_batch_zip
from app.services.permissions import can


class PermissionAndPackageTests(unittest.TestCase):
    def test_roles_have_expected_permissions(self):
        self.assertTrue(can("admin", "template_manage"))
        self.assertTrue(can("operator", "workflow_run"))
        self.assertFalse(can("viewer", "workflow_edit"))

    def test_batch_zip_contains_summary_and_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "result.xlsx"
            output.write_bytes(b"xlsx")
            archive = root / "batch.zip"
            summary = root / "summary.xlsx"
            build_batch_zip([SimpleNamespace(id=1, data_source_id=2, status="success", output_path=str(output), output_sha256="hash")], str(archive), str(summary))
            with ZipFile(archive) as package:
                self.assertEqual(set(package.namelist()), {"批次汇总.xlsx", "result.xlsx"})
