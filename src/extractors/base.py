"""Base extractor interface."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseExtractor(ABC):
    """Base class for all extractors."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.pages_dir = output_dir / "pages"
        self.renders_dir = output_dir / "renders"
        self.figures_dir = output_dir / "figures"

    def setup_directories(self):
        """Create output directories."""
        for d in [self.pages_dir, self.renders_dir, self.figures_dir]:
            d.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def extract(self, source: Path) -> dict:
        """Extract content from source. Returns extraction metadata."""
        pass

    @abstractmethod
    def extract_page(self, page_num: int, page_data) -> dict:
        """Extract content from a single page."""
        pass
