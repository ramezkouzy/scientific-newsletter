from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


DEFAULT_CONFIG_PATH = Path("config/newsletter.yaml")
EXAMPLE_CONFIG_PATH = Path("config/newsletter.example.yaml")
DEFAULT_REGISTRY_PATH = Path("data/sent_papers.json")


@dataclass
class Topic:
    name: str
    keywords: List[str]
    min_items: int = 2
    max_items: int = 5

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Topic":
        name = str(data.get("name", "")).strip()
        keywords = [str(k).strip() for k in data.get("keywords", []) if str(k).strip()]
        if not name:
            raise ValueError("Each topic needs a name.")
        if not keywords:
            raise ValueError(f"Topic {name!r} needs at least one keyword.")
        return cls(
            name=name,
            keywords=keywords,
            min_items=int(data.get("min_items", 2)),
            max_items=int(data.get("max_items", 5)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "keywords": self.keywords,
            "min_items": self.min_items,
            "max_items": self.max_items,
        }


@dataclass
class NewsletterConfig:
    newsletter: Dict[str, Any]
    schedule: Dict[str, Any]
    email: Dict[str, Any]
    discovery: Dict[str, Any]
    quality: Dict[str, Any]
    topics: List[Topic] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsletterConfig":
        required = ["newsletter", "schedule", "email", "discovery", "quality", "topics"]
        missing = [key for key in required if key not in data]
        if missing:
            raise ValueError(f"Missing config section(s): {', '.join(missing)}")
        topics = [Topic.from_dict(topic) for topic in data.get("topics", [])]
        if not topics:
            raise ValueError("At least one topic is required.")
        config = cls(
            newsletter=dict(data["newsletter"] or {}),
            schedule=dict(data["schedule"] or {}),
            email=dict(data["email"] or {}),
            discovery=dict(data["discovery"] or {}),
            quality=dict(data["quality"] or {}),
            topics=topics,
        )
        config.validate()
        return config

    def validate(self) -> None:
        name = str(self.newsletter.get("name", "")).strip()
        if not name:
            raise ValueError("newsletter.name is required.")
        if not self.email.get("sender_email"):
            raise ValueError("email.sender_email is required.")
        if not self.email.get("test_recipient"):
            raise ValueError("email.test_recipient is required.")
        if int(self.discovery.get("days_back", 0)) < 1:
            raise ValueError("discovery.days_back must be at least 1.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "newsletter": self.newsletter,
            "schedule": self.schedule,
            "email": self.email,
            "discovery": self.discovery,
            "quality": self.quality,
            "topics": [topic.to_dict() for topic in self.topics],
        }

    @property
    def name(self) -> str:
        return str(self.newsletter.get("name", "Scientific Newsletter"))

    @property
    def timezone(self) -> str:
        return str(self.newsletter.get("timezone", "UTC"))


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> NewsletterConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Config file not found at {path}. Run `scientific-newsletter setup` first."
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return NewsletterConfig.from_dict(data)


def write_config(config: NewsletterConfig, path: Path = DEFAULT_CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(config.to_dict(), sort_keys=False, allow_unicode=False),
        encoding="utf-8",
    )


def load_env_file(path: Path = Path(".env")) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def default_topics(selected: Optional[Iterable[str]] = None) -> List[Topic]:
    presets = {
        "cns oncology": Topic(
            "CNS Oncology",
            ["brain", "glioma", "glioblastoma", "brain metastases", "spine", "radiosurgery"],
        ),
        "radiation oncology": Topic(
            "Radiation Oncology",
            ["radiotherapy", "radiation therapy", "SBRT", "IMRT", "proton", "brachytherapy"],
        ),
        "ai in medicine": Topic(
            "AI in Medicine",
            ["artificial intelligence", "machine learning", "deep learning", "large language model"],
        ),
        "general oncology": Topic(
            "General Oncology",
            ["cancer", "immunotherapy", "chemotherapy", "survival", "phase 3", "randomized"],
        ),
        "general medicine": Topic(
            "General Medicine",
            ["cardiovascular", "diabetes", "infectious disease", "public health", "vaccine"],
        ),
    }
    if not selected:
        selected = [
            "cns oncology",
            "radiation oncology",
            "ai in medicine",
            "general oncology",
            "general medicine",
        ]
    topics = [
        Topic("Top Papers", ["randomized", "phase 3", "practice changing", "survival"], 3, 3)
    ]
    for item in selected:
        key = item.strip().lower()
        if not key:
            continue
        if key in presets:
            topics.append(presets[key])
        else:
            words = [part.strip() for part in key.replace("/", ",").split(",") if part.strip()]
            topics.append(Topic(item.strip().title(), words or [item.strip()], 2, 5))
    return topics


def build_config(
    *,
    name: str,
    sender_email: str,
    test_recipient: str,
    frequency: str,
    weekdays: List[str],
    run_time: str,
    timezone: str,
    topics: List[Topic],
    tone: str,
    email_mode: str,
    review_before_send: bool,
    contact_email: Optional[str] = None,
) -> NewsletterConfig:
    return NewsletterConfig.from_dict(
        {
            "newsletter": {
                "name": name,
                "description": "A clinician-curated digest of new scientific papers.",
                "audience": "Clinicians and scientists",
                "tone": tone,
                "timezone": timezone,
            },
            "schedule": {
                "frequency": frequency,
                "weekdays": weekdays,
                "time": run_time,
            },
            "email": {
                "mode": email_mode,
                "sender_email": sender_email,
                "sender_name": name,
                "test_recipient": test_recipient,
                "recipients": [],
                "review_before_send": review_before_send,
            },
            "discovery": {
                "days_back": 7,
                "max_results_per_topic": 20,
                "sources": {"pubmed": True, "semantic_scholar": True, "arxiv": True},
                "contact_email": contact_email or sender_email,
            },
            "quality": {
                "require_links": True,
                "require_result_data": True,
                "minimum_total_papers": 5,
                "rapid_fire_max": 8,
            },
            "topics": [topic.to_dict() for topic in topics],
        }
    )
