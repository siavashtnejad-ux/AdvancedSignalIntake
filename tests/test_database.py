from pathlib import Path
from tempfile import TemporaryDirectory
from backend.database import Database

def test_db_roundtrip():
    with TemporaryDirectory() as d:
        db=Database(Path(d)/"test.db");db.init()
        sid=db.create_scan({"query":"x","sources":["pubmed"],"max_results":10,"from_year":2024,"to_year":2026,"iran_focus":False})
        assert sid==1
        assert db.get_scan(sid)["query"]=="x"
