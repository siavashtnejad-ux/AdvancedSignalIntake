from __future__ import annotations
import xml.etree.ElementTree as ET
import asyncio
from datetime import date
from urllib.parse import quote
from backend.connectors.base import BaseConnector
from backend.models import ConnectorResult, EvidenceRecord, ScanRequest
from backend.config import settings

class PubMedConnector(BaseConnector):
    code = "pubmed"
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def _common(self) -> dict[str, str]:
        p={"tool":"ethical_horizon"}
        if settings.ncbi_email: p["email"]=settings.ncbi_email
        if settings.ncbi_api_key: p["api_key"]=settings.ncbi_api_key
        return p

    def _query(self, req: ScanRequest) -> str:
        q=req.query.strip()
        if req.iran_focus:
            q=f"({q}) AND (Iran[Title/Abstract] OR Iranian[Title/Abstract] OR Iran[Affiliation])"
        if req.from_year or req.to_year:
            start=req.from_year or 1900
            end=req.to_year or date.today().year
            q=f'({q}) AND ("{start}/01/01"[Date - Publication] : "{end}/12/31"[Date - Publication])'
        return q

    async def search(self, request: ScanRequest) -> ConnectorResult:
        q=self._query(request)
        warnings=[]
        async with self.client() as client:
            params={**self._common(),"db":"pubmed","term":q,"retmode":"json","retmax":str(request.max_results),"sort":"pub_date"}
            r=await client.get(f"{self.BASE}/esearch.fcgi",params=params)
            r.raise_for_status()
            data=r.json().get("esearchresult",{})
            ids=data.get("idlist",[])
            total=int(data.get("count") or 0)
            if not ids:
                return ConnectorResult(source=self.code,total=total,records=[],warnings=warnings)

            # Avoid exceeding NCBI's ordinary unauthenticated cadence.
            if not settings.ncbi_api_key:
                await asyncio.sleep(0.36)

            fparams={**self._common(),"db":"pubmed","id":",".join(ids),"retmode":"xml"}
            fr=await client.get(f"{self.BASE}/efetch.fcgi",params=fparams)
            fr.raise_for_status()
            records=self._parse(fr.text)
            return ConnectorResult(source=self.code,total=total,records=records,warnings=warnings)

    def _parse(self, xml_text: str) -> list[EvidenceRecord]:
        root=ET.fromstring(xml_text)
        out=[]
        for item in root.findall(".//PubmedArticle"):
            citation=item.find("MedlineCitation")
            article=citation.find("Article") if citation is not None else None
            if article is None: continue
            pmid=(citation.findtext("PMID") or "").strip()
            title="".join(article.find("ArticleTitle").itertext()).strip() if article.find("ArticleTitle") is not None else "Untitled"
            abstract_parts=[]
            for a in article.findall(".//Abstract/AbstractText"):
                label=a.attrib.get("Label")
                text="".join(a.itertext()).strip()
                if text: abstract_parts.append(f"{label}: {text}" if label else text)
            abstract=" ".join(abstract_parts)
            authors=[]
            affiliations=[]
            for a in article.findall(".//AuthorList/Author"):
                collective=a.findtext("CollectiveName")
                if collective:
                    authors.append(collective.strip())
                else:
                    name=" ".join(filter(None,[(a.findtext("ForeName") or "").strip(),(a.findtext("LastName") or "").strip()])).strip()
                    if name: authors.append(name)
                for aff in a.findall(".//AffiliationInfo/Affiliation"):
                    if aff.text: affiliations.append(aff.text.strip())
            journal=article.findtext(".//Journal/Title") or article.findtext(".//Journal/ISOAbbreviation") or ""
            pubdate=article.find(".//JournalIssue/PubDate")
            year=None; date_text=None
            if pubdate is not None:
                y=pubdate.findtext("Year")
                med=pubdate.findtext("MedlineDate")
                if y and y.isdigit(): year=int(y)
                elif med:
                    import re
                    m=re.search(r"(19|20)\d{2}",med)
                    if m: year=int(m.group(0))
                month=pubdate.findtext("Month") or ""
                day=pubdate.findtext("Day") or ""
                date_text="-".join(x for x in [str(year) if year else "",month,day] if x) or med
            doi=None
            for aid in item.findall(".//PubmedData/ArticleIdList/ArticleId"):
                if aid.attrib.get("IdType")=="doi":
                    doi=(aid.text or "").strip() or None
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else ""
            out.append(EvidenceRecord(
                source=self.code,external_id=pmid,evidence_type="publication",
                title=title,abstract=abstract,publication_date=date_text,year=year,url=url,doi=doi,
                authors=authors,affiliations=list(dict.fromkeys(affiliations)),
                metadata={"journal":journal,"pmid":pmid}
            ))
        return out
