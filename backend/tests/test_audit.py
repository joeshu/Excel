import tempfile
import unittest
from pathlib import Path

from app.services.audit import sha256_file


class AuditTests(unittest.TestCase):
    def test_sha256_file_is_stable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.xlsx"
            path.write_bytes(b"excel-result")
            self.assertEqual(sha256_file(str(path)), "6799dfcf011a305fb103b67e3c12bd2197cfb933100e97f42be4c23a53e19115")
