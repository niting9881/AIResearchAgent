"""arXiv paper scraper using arxiv API"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import arxiv

from src.utils.config import settings
from src.utils.helpers import clean_text, generate_id
from src.utils.logger import app_logger


class ArxivScraper:
    """Scraper for arXiv papers"""

    def __init__(self):
        self.client = arxiv.Client()
        self.search_query = settings.arxiv_search_query

    def search_papers(
        self,
        query: Optional[str] = None,
        max_results: int = 50,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Search for papers on arXiv
        
        Args:
            query: Search query (uses default if None)
            max_results: Maximum number of results
            start_date: Filter papers published after this date
            end_date: Filter papers published before this date
            
        Returns:
            List of paper dictionaries
        """
        query = query or self.search_query
        
        app_logger.info(f"Searching arXiv with query: {query}")
        app_logger.info(f"Max results: {max_results}")
        
        try:
            # Create search
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            
            papers = []
            
            for result in self.client.results(search):
                # Filter by date if specified
                if start_date and result.published < start_date:
                    continue
                if end_date and result.published > end_date:
                    continue
                
                paper = self._parse_paper(result)
                papers.append(paper)
            
            app_logger.info(f"Found {len(papers)} papers from arXiv")
            return papers
            
        except Exception as e:
            app_logger.error(f"Error searching arXiv: {e}")
            raise

    def get_recent_papers(self, days: int = 7, max_results: int = 50) -> List[Dict]:
        """
        Get papers published in the last N days
        
        Args:
            days: Number of days to look back
            max_results: Maximum number of results
            
        Returns:
            List of recent papers
        """
        start_date = datetime.now() - timedelta(days=days)
        return self.search_papers(
            max_results=max_results,
            start_date=start_date
        )

    def _parse_paper(self, result: arxiv.Result) -> Dict:
        """
        Parse arxiv result into standardized format
        
        Args:
            result: arxiv.Result object
            
        Returns:
            Parsed paper dictionary
        """
        paper_id = result.entry_id.split('/')[-1]
        
        return {
            "id": generate_id(paper_id),
            "source": "arxiv",
            "source_id": paper_id,
            "title": clean_text(result.title),
            "authors": [author.name for author in result.authors],
            "abstract": clean_text(result.summary),
            "published": result.published.isoformat(),
            "updated": result.updated.isoformat() if result.updated else None,
            "url": result.entry_id,
            "pdf_url": result.pdf_url,
            "categories": result.categories,
            "primary_category": result.primary_category,
            "comment": result.comment,
            "journal_ref": result.journal_ref,
            "doi": result.doi,
            "citations": 0,  # arXiv API doesn't provide citation count
            "scraped_at": datetime.utcnow().isoformat(),
        }

    def download_pdf(self, paper_id: str, output_dir: str) -> str:
        """
        Download PDF for a paper
        
        Args:
            paper_id: arXiv paper ID
            output_dir: Directory to save PDF
            
        Returns:
            Path to downloaded PDF
        """
        try:
            search = arxiv.Search(id_list=[paper_id])
            paper = next(self.client.results(search))
            
            filepath = paper.download_pdf(dirpath=output_dir)
            app_logger.info(f"Downloaded PDF for {paper_id} to {filepath}")
            return filepath
            
        except Exception as e:
            app_logger.error(f"Error downloading PDF for {paper_id}: {e}")
            raise


# Example usage
if __name__ == "__main__":
    scraper = ArxivScraper()
    
    # Get initial 50 papers
    papers = scraper.search_papers(max_results=50)
    print(f"Found {len(papers)} papers")
    
    # Print first paper
    if papers:
        print("\nFirst paper:")
        print(f"Title: {papers[0]['title']}")
        print(f"Authors: {', '.join(papers[0]['authors'][:3])}")
        print(f"Published: {papers[0]['published']}")
