from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class CandidateNote:
    """A note candidate for context compilation."""

    title: str
    path: Path
    tags: set[str]
    category: str | None
    snippet: str
    modified_time: datetime
