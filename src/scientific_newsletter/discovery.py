from __future__ import annotations

import json
import os
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List

from .config import NewsletterConfig, Topic
from .registry import deduplicate_papers


ssl._create_default_https_context = ssl.create_default_context


def _request_json(url: str, *, headers: Dict[str, str], timeout: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _request_bytes(url: str, *, headers: Dict[str, str], timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _user_agent(config: NewsletterConfig) -> str:
    contact = config.discovery.get("contact_email") or config.email.get("sender_email") or "unknown@example.com"
    return f"scientific-newsletter/0.1 (mailto:{contact})"


def _topic_query(topic: Topic) -> str:
    return " OR ".join(f'"{keyword}"' for keyword in topic.keywords[:8])


def _pubmed_date(article: ET.Element) -> str:
    article_date = article.find(".//ArticleDate")
    if article_date is not None:
        year = article_date.findtext("Year")
        month = article_date.findtext("Month") or "01"
        day = article_date.findtext("Day") or "01"
        if year:
            return f"{year}-{int(month):02d}-{int(day):02d}"
    pub_date = article.find(".//PubDate")
    if pub_date is not None:
        year = pub_date.findtext("Year")
        month = pub_date.findtext("Month") or "01"
        day = pub_date.findtext("Day") or "01"
        month_map = {
            "jan": 1,
            "feb": 2,
            "mar": 3,
            "apr": 4,
            "may": 5,
            "jun": 6,
            "jul": 7,
            "aug": 8,
            "sep": 9,
            "oct": 10,
            "nov": 11,
            "dec": 12,
        }
        if year:
            if not str(month).isdigit():
                month = month_map.get(str(month).lower()[:3], 1)
            return f"{year}-{int(month):02d}-{int(day):02d}"
    return ""


def _parse_pubmed_xml(raw: bytes) -> List[Dict[str, Any]]:
    root = ET.fromstring(raw)
    papers: List[Dict[str, Any]] = []
    for article in root.findall(".//PubmedArticle"):
        pmid = article.findtext(".//MedlineCitation/PMID") or ""
        title = " ".join(" ".join(article.findtext(".//ArticleTitle", "") .split()).split())
        abstract = " ".join(
            " ".join(node.itertext()).strip()
            for node in article.findall(".//Abstract/AbstractText")
            if " ".join(node.itertext()).strip()
        )
        journal = article.findtext(".//Journal/Title") or article.findtext(".//ISOAbbreviation") or ""
        doi = ""
        for node in article.findall(".//ArticleId"):
            if node.get("IdType") == "doi":
                doi = (node.text or "").strip()
                break
        authors = []
        for author in article.findall(".//AuthorList/Author")[:5]:
            last = author.findtext("LastName")
            initials = author.findtext("Initials")
            if last:
                authors.append(f"{last} {initials or ''}".strip())
        if title:
            papers.append(
                {
                    "title": title,
                    "original_title": title,
                    "abstract": abstract,
                    "journal": journal,
                    "doi": doi,
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else "",
                    "published": _pubmed_date(article),
                    "authors": authors,
                    "source": "PubMed",
                }
            )
    return papers


def search_pubmed(topic: Topic, config: NewsletterConfig) -> List[Dict[str, Any]]:
    days_back = int(config.discovery.get("days_back", 7))
    max_results = int(config.discovery.get("max_results_per_topic", 20))
    today = date.today()
    start = today - timedelta(days=days_back)
    query = f"({_topic_query(topic)}) AND ({start:%Y/%m/%d}:{today:%Y/%m/%d}[Date - Publication])"
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "retmode": "json",
        "retmax": str(max_results),
        "sort": "pub_date",
        "term": query,
    }
    headers = {"User-Agent": _user_agent(config)}
    data = _request_json(f"{base}?{urllib.parse.urlencode(params)}", headers=headers)
    ids = data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        return []
    fetch_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    fetch_params = {"db": "pubmed", "retmode": "xml", "id": ",".join(ids)}
    raw = _request_bytes(f"{fetch_base}?{urllib.parse.urlencode(fetch_params)}", headers=headers)
    return _parse_pubmed_xml(raw)


def search_semantic_scholar(topic: Topic, config: NewsletterConfig) -> List[Dict[str, Any]]:
    max_results = min(int(config.discovery.get("max_results_per_topic", 20)), 100)
    query = " ".join(topic.keywords[:5])
    fields = "title,abstract,venue,url,authors,externalIds,publicationDate,year"
    params = urllib.parse.urlencode({"query": query, "limit": max_results, "fields": fields})
    headers = {"User-Agent": _user_agent(config)}
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        headers["x-api-key"] = api_key
    data = _request_json(f"https://api.semanticscholar.org/graph/v1/paper/search?{params}", headers=headers)
    papers = []
    for item in data.get("data", []):
        external = item.get("externalIds") or {}
        doi = external.get("DOI") or ""
        title = item.get("title") or ""
        if not title:
            continue
        papers.append(
            {
                "title": title,
                "original_title": title,
                "abstract": item.get("abstract") or "",
                "journal": item.get("venue") or "",
                "doi": doi,
                "url": item.get("url") or (f"https://doi.org/{doi}" if doi else ""),
                "published": item.get("publicationDate") or str(item.get("year") or ""),
                "authors": [author.get("name", "") for author in item.get("authors", [])[:5]],
                "source": "Semantic Scholar",
            }
        )
    return papers


def search_arxiv(topic: Topic, config: NewsletterConfig) -> List[Dict[str, Any]]:
    max_results = min(int(config.discovery.get("max_results_per_topic", 20)), 50)
    query = " OR ".join(f'all:"{keyword}"' for keyword in topic.keywords[:4])
    params = urllib.parse.urlencode(
        {
            "search_query": query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    headers = {"User-Agent": _user_agent(config)}
    raw = _request_bytes(f"https://export.arxiv.org/api/query?{params}", headers=headers)
    root = ET.fromstring(raw)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    papers = []
    for entry in root.findall("atom:entry", ns):
        title = " ".join((entry.findtext("atom:title", default="", namespaces=ns) or "").split())
        abstract = " ".join((entry.findtext("atom:summary", default="", namespaces=ns) or "").split())
        url = entry.findtext("atom:id", default="", namespaces=ns) or ""
        published = (entry.findtext("atom:published", default="", namespaces=ns) or "")[:10]
        authors = [
            author.findtext("atom:name", default="", namespaces=ns) or ""
            for author in entry.findall("atom:author", ns)[:5]
        ]
        if title:
            papers.append(
                {
                    "title": title,
                    "original_title": title,
                    "abstract": abstract,
                    "journal": "arXiv",
                    "doi": "",
                    "url": url,
                    "published": published,
                    "authors": authors,
                    "source": "arXiv",
                }
            )
    return papers


def discover(config: NewsletterConfig) -> List[Dict[str, Any]]:
    sources = config.discovery.get("sources", {})
    papers: List[Dict[str, Any]] = []
    for topic in config.topics:
        if topic.name.lower().startswith("top"):
            continue
        if sources.get("pubmed", True):
            try:
                papers.extend(search_pubmed(topic, config))
                time.sleep(0.34)
            except Exception as exc:
                papers.append({"title": f"PubMed search failed for {topic.name}", "error": str(exc), "source": "PubMed"})
        if sources.get("semantic_scholar", True):
            try:
                papers.extend(search_semantic_scholar(topic, config))
                time.sleep(1.0)
            except Exception as exc:
                papers.append(
                    {"title": f"Semantic Scholar search failed for {topic.name}", "error": str(exc), "source": "Semantic Scholar"}
                )
        if sources.get("arxiv", True) and any("ai" in keyword.lower() or "machine" in keyword.lower() for keyword in topic.keywords):
            try:
                papers.extend(search_arxiv(topic, config))
                time.sleep(3.0)
            except Exception as exc:
                papers.append({"title": f"arXiv search failed for {topic.name}", "error": str(exc), "source": "arXiv"})
    return [paper for paper in deduplicate_papers(papers) if not paper.get("error")]
