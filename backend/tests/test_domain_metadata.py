import tempfile
import unittest
from pathlib import Path

from app.services.domain_metadata import field_signature, file_sha256


class DomainMetadataTests(unittest.TestCase):
    def test_field_signature_is_order_independent(self):
        self.assertEqual(field_signature(["region", "amount", "region"]), field_signature(["amount", "region"]))

    def test_file_hash_is_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.csv"
            path.write_text("id,amount\n1,2\n", encoding="utf-8")
            self.assertEqual(file_sha256(str(path)), file_sha256(str(path)))
