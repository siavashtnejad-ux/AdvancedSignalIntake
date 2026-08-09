from __future__ import annotations
from datetime import date
from backend.connectors.base import BaseConnector
from backend.models import ConnectorResult, EvidenceRecord, ScanRequest

def deep(obj, path, default=None):
    cur=obj
    for part in path.split("."):
        if not isinstance(cur,dict) or part not in cur: return default
        cur=cur[part]
    return cur

class ClinicalTrialsConnector(BaseConnector):
    code="clinicaltrials"
    BASE="https://clinicaltrials.gov/api/v2/studies"

    async def search(self, request: ScanRequest) -> ConnectorResult:
        query=request.query.strip()
        if request.iran_focus:
            query=f"({query}) AND AREA[LocationCountry]Iran"
        params={
            "query.term":query,
            "pageSize":str(min(request.max_results,100)),
            "format":"json",
            "countTotal":"true",
        }
        warnings=[]
        async with self.client() as client:
            r=await client.get(self.BASE,params=params)
            r.raise_for_status()
            data=r.json()
        studies=data.get("studies",[])
        total=int(data.get("totalCount") or len(studies))
        records=[]
        for s in studies:
            p=s.get("protocolSection",{})
            nct=deep(p,"identificationModule.nctId","")
            title=deep(p,"identificationModule.briefTitle","") or deep(p,"identificationModule.officialTitle","") or "Untitled study"
            status=deep(p,"statusModule.overallStatus","")
            start=deep(p,"statusModule.startDateStruct.date")
            year=None
            if isinstance(start,str) and len(start)>=4 and start[:4].isdigit():
                year=int(start[:4])
            if request.from_year and year and year<request.from_year: continue
            if request.to_year and year and year>request.to_year: continue
            summary=deep(p,"descriptionModule.briefSummary","") or deep(p,"descriptionModule.detailedDescription","") or ""
            conditions=deep(p,"conditionsModule.conditions",[]) or []
            phases=deep(p,"designModule.phases",[]) or []
            study_type=deep(p,"designModule.studyType","")
            sponsor=deep(p,"sponsorCollaboratorsModule.leadSponsor.name","")
            interventions=[]
            for i in deep(p,"armsInterventionsModule.interventions",[]) or []:
                name=i.get("name")
                if name: interventions.append(name)
            locations=deep(p,"contactsLocationsModule.locations",[]) or []
            affiliations=[]
            countries=[]
            iran_locations=[]
            for loc in locations:
                facility=loc.get("facility")
                city=loc.get("city")
                country=loc.get("country")
                label=", ".join(x for x in [facility,city,country] if x)
                if label: affiliations.append(label)
                if country: countries.append(country)
                if (country or "").lower()=="iran": iran_locations.append(label or "Iran")
            records.append(EvidenceRecord(
                source=self.code,external_id=nct,evidence_type="clinical_trial",
                title=title,abstract=summary,publication_date=start,year=year,
                url=f"https://clinicaltrials.gov/study/{nct}" if nct else "",
                authors=[sponsor] if sponsor else [],affiliations=affiliations,
                metadata={
                    "status":status,"phases":phases,"study_type":study_type,
                    "conditions":conditions,"interventions":interventions,
                    "countries":countries,"iran_locations":iran_locations,
                    "sponsor":sponsor
                }
            ))
        return ConnectorResult(source=self.code,total=total,records=records,warnings=warnings)
