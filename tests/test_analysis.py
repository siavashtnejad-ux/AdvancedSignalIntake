from backend.models import EvidenceRecord
from backend.analysis.engine import analyze_signal

def sample():
    return [
        EvidenceRecord(
            source="pubmed",external_id="1",title="Novel AI clinical decision support for cancer",
            abstract="Prospective validation raises algorithmic bias, privacy, accountability and informed consent concerns.",
            year=2026,url="",authors=[],affiliations=["Tehran University of Medical Sciences"],metadata={}
        ),
        EvidenceRecord(
            source="clinicaltrials",external_id="NCT1",evidence_type="clinical_trial",
            title="AI diagnostic clinical trial",abstract="Recruiting multicenter validation study.",
            year=2026,url="",authors=[],affiliations=["Tehran, Iran"],
            metadata={"status":"RECRUITING","phases":["PHASE2"],"countries":["Iran"]}
        ),
    ]

def test_signal_analysis():
    s=analyze_signal("AI cancer diagnosis",sample(),{"pubmed":100,"clinicaltrials":5},[])
    assert 0 <= s.signal_score <= 100
    assert s.ethics.score > 0
    assert s.iran.score > 0
    assert s.clinical_activity_score > 0
