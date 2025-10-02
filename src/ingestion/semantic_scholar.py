"""Semantic Scholar paper scraper using their API"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import requests

from src.utils.config import settings
from src.utils.helpers import clean_text, generate_id
from src.utils.logger import app_logger


class SemanticScholarScraper:
    """Scraper for Semantic Scholar papers"""

    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1"
        self.search_query = settings.semantic_scholar_query
        # Rate limiting: 100 requests per 5 minutes
        self.rate_limit_delay = 3  # seconds between requests

    def search_papers(
        self,
        query: Optional[str] = None,
        max_results: int = 50,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        min_citations: int = 0,
    ) -> List[Dict]:
        """
        Search for papers on Semantic Scholar
        
        Args:
            query: Search query (uses default if None)
            max_results: Maximum number of results
            year_from: Filter papers from this year
            year_to: Filter papers up to this year
            min_citations: Minimum citation count
            
        Returns:
            List of paper dictionaries
        """
        query = query or self.search_query
        
        app_logger.info(f"Searching Semantic Scholar with query: {query}")
        app_logger.info(f"Max results: {max_results}")
        
        try:
            papers = []
            offset = 0
            limit = min(100, max_results)  # API limit is 100 per request
            
            while len(papers) < max_results:
                # Build query parameters
                params = {
                    "query": query,
                    "offset": offset,
                    "limit": limit,
                    "fields": "paperId,title,abstract,authors,year,citationCount,url,venue,publicationDate,externalIds",
                }
                
                # Add year filter if specified
                if year_from:
                    params["year"] = f"{year_from}-"
                if year_to:
                    if year_from:
                        params["year"] = f"{year_from}-{year_to}"
                    else:
                        params["year"] = f"-{year_to}"
                
                # Make request
                response = requests.get(
                    f"{self.base_url}/paper/search",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                results = data.get("data", [])
                
                if not results:
                    break
                
                # Parse and filter papers
                for result in results:
                    if len(papers) >= max_results:
                        break
                    
                    # Filter by citations
                    if result.get("citationCount", 0) < min_citations:
                        continue
                    
                    paper = self._parse_paper(result)
                    papers.append(paper)
                
                offset += limit
                
                # Rate limiting
                time.sleep(self.rate_limit_delay)
                
                # Check if we've reached the end
                if len(results) < limit:
                    break
            
            app_logger.info(f"Found {len(papers)} papers from Semantic Scholar")
            return papers
            
        except requests.exceptions.RequestException as e:
            app_logger.error(f"Error searching Semantic Scholar: {e}")
            raise
        except Exception as e:
            app_logger.error(f"Unexpected error: {e}")
            raise

    def get_paper_by_id(self, paper_id: str) -> Optional[Dict]:
        """
        Get detailed paper information by ID
        
        Args:
            paper_id: Semantic Scholar paper ID
            
        Returns:
            Paper dictionary or None
        """
        try:
            response = requests.get(
                f"{self.base_url}/paper/{paper_id}",
                params={
                    "fields": "paperId,title,abstract,authors,year,citationCount,url,venue,publicationDate,externalIds,references,citations"
                },
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return self._parse_paper(result)
            
        except requests.exceptions.RequestException as e:
            app_logger.error(f"Error fetching paper {paper_id}: {e}")
            return None

    def get_recent_papers(
        self,
        days: int = 7,
        max_results: int = 50,
        min_citations: int = 0
    ) -> List[Dict]:
        """
        Get papers published in the last N days
        
        Args:
            days: Number of days to look back
            max_results: Maximum number of results
            min_citations: Minimum citation count
            
        Returns:
            List of recent papers
        """
        current_year = datetime.now().year
        start_date = datetime.now() - timedelta(days=days)
        
        # Semantic Scholar uses years, not exact dates
        year_from = start_date.year
        
        return self.search_papers(
            max_results=max_results,
            year_from=year_from,
            year_to=current_year,
            min_citations=min_citations
        )

    def _parse_paper(self, result: Dict) -> Dict:
        """
        Parse Semantic Scholar result into standardized format
        
        Args:
            result: API result dictionary
            
        Returns:
            Parsed paper dictionary
        """
        paper_id = result.get("paperId", "")
        
        # Extract authors
        authors = []
        for author in result.get("authors", []):
            author_name = author.get("name", "")
            if author_name:
                authors.append(author_name)
        
        # Extract external IDs
        external_ids = result.get("externalIds", {})
        arxiv_id = external_ids.get("ArXiv")
        doi = external_ids.get("DOI")
        
        # Parse publication date
        pub_date = result.get("publicationDate") or result.get("year")
        if pub_date:
            try:
                if isinstance(pub_date, int):
                    pub_date = f"{pub_date}-01-01"
                published = datetime.fromisoformat(pub_date).isoformat()
            except:
                published = pub_date
        else:
            published = None
        
        return {
            "id": generate_id(paper_id),
            "source": "semantic_scholar",
            "source_id": paper_id,
            "title": clean_text(result.get("title", "")),
            "authors": authors,
            "abstract": clean_text(result.get("abstract", "")),
            "published": published,
            "updated": None,
            "url": result.get("url", f"https://www.semanticscholar.org/paper/{paper_id}"),
            "pdf_url": None,  # Semantic Scholar doesn't directly provide PDF URLs
            "categories": [result.get("venue", "")] if result.get("venue") else [],
            "primary_category": result.get("venue"),
            "comment": None,
            "journal_ref": result.get("venue"),
            "doi": doi,
            "arxiv_id": arxiv_id,
            "citations": result.get("citationCount", 0),
            "year": result.get("year"),
            "scraped_at": datetime.utcnow().isoformat(),
        }


# Example usage
if __name__ == "__main__":
    scraper = SemanticScholarScraper()
    
    # Get initial 50 papers
    papers = scraper.search_papers(max_results=50, min_citations=10)
    print(f"Found {len(papers)} papers")
    
    # Print first paper
    if papers:
        print("\nFirst paper:")
        print(f"Title: {papers[0]['title']}")
        print(f"Authors: {', '.join(papers[0]['authors'][:3])}")
        print(f"Citations: {papers[0]['citations']}")
        print(f"Published: {papers[0]['published']}")
