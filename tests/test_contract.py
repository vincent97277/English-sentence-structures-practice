import json
import subprocess
import sys
import tempfile
from pathlib import Path
from jsonschema import Draft202012Validator
from tests.support import RuntimeFixture
from sentence_practice import Practice
from sentence_practice.materials import load_json


class ContractTests(RuntimeFixture):
    def test_standard_schema_examples_and_duplicate_json_keys(self):
        project=Path(__file__).parents[1]
        schema=json.loads((project/'schemas/material-pack-v1.schema.json').read_text())
        Draft202012Validator.check_schema(schema)
        validator=Draft202012Validator(schema)
        for path in (project/'examples').glob('material-pack-v1-*.json'):
            validator.validate(json.loads(path.read_text()))
        pack={"format":"sentence-materials/v1","source":"fixture","items":[{"pattern":"I think + clause","purpose":"看法","examples":["I think this works."]}]}
        validator.validate(pack)
        for fields in ({"notes":[]},{"purpose":" "},{"unknown":1},{"examples":[]},{"id":"outside"},{"priority":"Low"}):
            invalid={**pack,"items":[{**pack['items'][0],**fields}]}
            self.assertTrue(list(validator.iter_errors(invalid)))
        with self.assertRaises(ValueError):
            load_json('{"source":"first","source":"second"}')
        with self.assertRaises(ValueError):
            load_json('{"value":NaN}')

    def test_cli_enforces_explicit_project_identity_and_reports_failure(self):
        self.seed()
        cli=Path(__file__).parents[1]/'plugins/sentence-structures/scripts/practice.py'
        request=self.root/'request.json'
        request.write_text(json.dumps({"operation":"progress","project_id":"wrong","payload":{}}))
        failed=subprocess.run([sys.executable,str(cli),'--root',str(self.root),'--request',str(request)],capture_output=True,text=True)
        self.assertEqual(failed.returncode,1)
        self.assertTrue(json.loads(failed.stdout)['stop_questions'])
        marker=json.loads((self.root/'data/project.json').read_text())
        request.write_text(json.dumps({"operation":"progress","project_id":marker['project_id'],"payload":{}}))
        succeeded=subprocess.run([sys.executable,str(cli),'--root',str(self.root),'--request',str(request)],capture_output=True,text=True)
        self.assertEqual(succeeded.returncode,0)
        self.assertEqual(json.loads(succeeded.stdout)['status'],'ok')

    def test_standalone_export_restore_and_missing_database_does_not_initialize(self):
        self.seed()
        session=self.call('start')
        self.produce(session,'工作',kind='end')
        self.call('finish',session_id=session['id'])
        checkpoint=self.call('export')['checkpoint']
        with tempfile.TemporaryDirectory() as folder:
            clone=Practice(Path(folder))
            restored=clone.execute({'operation':'restore','payload':{'checkpoint':checkpoint}})
            self.assertEqual(restored['mode'],'standalone restore')
            progress=clone.execute({'operation':'progress'})
            self.assertEqual(progress['materials'][0]['uses'],1)
        (self.root/'data/practice.sqlite3').unlink()
        with self.assertRaises(ValueError):
            self.call('progress')
        self.assertFalse((self.root/'data/practice.sqlite3').exists())
