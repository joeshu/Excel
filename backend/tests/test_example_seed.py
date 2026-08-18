import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.data_source import DataSource
from app.models.template import Template
from app.models.workflow import WorkflowDef
from app.services.example_seed import seed_examples


class ExampleSeedTests(unittest.TestCase):
    def test_seed_is_idempotent_and_creates_reference_workflows(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine)
        with tempfile.TemporaryDirectory() as directory:
            with patch("app.services.example_seed.settings.upload_dir", directory):
                with patch("app.services.example_seed.example_root", return_value=Path(__file__).parents[2] / "sample_data" / "scenarios"):
                    with session_factory() as db:
                        seed_examples(db)
                        seed_examples(db)
                        self.assertEqual(db.scalar(select(func.count()).select_from(Template).where(Template.is_example.is_(True))), 4)
                        self.assertEqual(db.scalar(select(func.count()).select_from(DataSource).where(DataSource.is_example.is_(True))), 4)
                        self.assertEqual(db.scalar(select(func.count()).select_from(WorkflowDef).where(WorkflowDef.is_example.is_(True))), 5)
                        dag = db.scalar(select(WorkflowDef).where(WorkflowDef.name.like("%模式 B%")))
                        self.assertIsNotNone(dag)
                        self.assertEqual(dag.node_json["nodes"][0]["data"]["config"]["source_id"], db.scalar(select(DataSource.id).where(DataSource.name == "示例数据：basic_no_formula")))


if __name__ == "__main__":
    unittest.main()
