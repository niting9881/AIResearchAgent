"""Document chunking strategies for RAG"""

from typing import Dict, List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter

from src.utils.config import settings
from src.utils.helpers import clean_text, count_tokens, generate_id
from src.utils.logger import app_logger


class DocumentChunker:
    """Chunks documents for optimal retrieval"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        length_function: callable = len,
    ):
        """
        Initialize document chunker
        
        Args:
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
            length_function: Function to measure chunk length
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=length_function,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def chunk_paper(self, paper: Dict) -> List[Dict]:
        """
        Chunk a single research paper
        
        Args:
            paper: Paper dictionary with metadata
            
        Returns:
            List of chunk dictionaries
        """
        # Combine title and abstract for chunking
        title = paper.get("title", "")
        abstract = paper.get("abstract", "")
        
        # Create full text
        full_text = f"Title: {title}\n\nAbstract: {abstract}"
        full_text = clean_text(full_text)
        
        # Split into chunks
        text_chunks = self.text_splitter.split_text(full_text)
        
        chunks = []
        for idx, chunk_text in enumerate(text_chunks):
            chunk = {
                "id": generate_id(f"{paper['id']}_{idx}"),
                "paper_id": paper["id"],
                "chunk_index": idx,
                "content": chunk_text,
                "token_count": count_tokens(chunk_text),
                "metadata": {
                    "title": title,
                    "authors": paper.get("authors", []),
                    "published": paper.get("published", ""),
                    "source": paper.get("source", ""),
                    "url": paper.get("url", ""),
                    "categories": paper.get("categories", []),
                    "citations": paper.get("citations", 0),
                    "chunk_index": idx,
                    "total_chunks": len(text_chunks),
                },
            }
            chunks.append(chunk)
        
        return chunks

    def chunk_documents(self, papers: List[Dict]) -> List[Dict]:
        """
        Chunk multiple papers
        
        Args:
            papers: List of paper dictionaries
            
        Returns:
            List of all chunks from all papers
        """
        all_chunks = []
        
        for paper in papers:
            try:
                chunks = self.chunk_paper(paper)
                all_chunks.extend(chunks)
            except Exception as e:
                app_logger.error(f"Error chunking paper {paper.get('id', 'unknown')}: {e}")
                continue
        
        app_logger.info(f"Created {len(all_chunks)} chunks from {len(papers)} papers")
        return all_chunks


class SemanticChunker:
    """Advanced semantic-aware chunking"""

    def __init__(self, max_chunk_size: int = 1000):
        self.max_chunk_size = max_chunk_size

    def chunk_by_sections(self, paper: Dict) -> List[Dict]:
        """
        Chunk paper by logical sections (title, abstract, body)
        
        Args:
            paper: Paper dictionary
            
        Returns:
            List of section-based chunks
        """
        chunks = []
        paper_id = paper["id"]
        
        # Chunk 1: Title + Authors
        if paper.get("title"):
            chunks.append({
                "id": generate_id(f"{paper_id}_title"),
                "paper_id": paper_id,
                "chunk_index": 0,
                "content": f"Title: {paper['title']}\nAuthors: {', '.join(paper.get('authors', [])[:5])}",
                "section": "title",
                "metadata": self._create_metadata(paper, "title", 0),
            })
        
        # Chunk 2: Abstract
        if paper.get("abstract"):
            abstract_text = f"Abstract:\n{paper['abstract']}"
            
            # If abstract is too long, split it
            if len(abstract_text) > self.max_chunk_size:
                splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.max_chunk_size,
                    chunk_overlap=100,
                )
                abstract_chunks = splitter.split_text(abstract_text)
                
                for idx, chunk_text in enumerate(abstract_chunks):
                    chunks.append({
                        "id": generate_id(f"{paper_id}_abstract_{idx}"),
                        "paper_id": paper_id,
                        "chunk_index": len(chunks),
                        "content": chunk_text,
                        "section": "abstract",
                        "metadata": self._create_metadata(paper, "abstract", len(chunks)),
                    })
            else:
                chunks.append({
                    "id": generate_id(f"{paper_id}_abstract"),
                    "paper_id": paper_id,
                    "chunk_index": len(chunks),
                    "content": abstract_text,
                    "section": "abstract",
                    "metadata": self._create_metadata(paper, "abstract", len(chunks)),
                })
        
        return chunks

    def _create_metadata(self, paper: Dict, section: str, chunk_idx: int) -> Dict:
        """Create metadata for a chunk"""
        return {
            "title": paper.get("title", ""),
            "authors": paper.get("authors", []),
            "published": paper.get("published", ""),
            "source": paper.get("source", ""),
            "url": paper.get("url", ""),
            "categories": paper.get("categories", []),
            "citations": paper.get("citations", 0),
            "section": section,
            "chunk_index": chunk_idx,
        }


def chunk_documents(papers: List[Dict], strategy: str = "recursive") -> List[Dict]:
    """
    Convenience function to chunk documents
    
    Args:
        papers: List of paper dictionaries
        strategy: Chunking strategy ('recursive' or 'semantic')
        
    Returns:
        List of chunks
    """
    if strategy == "semantic":
        chunker = SemanticChunker()
        all_chunks = []
        for paper in papers:
            chunks = chunker.chunk_by_sections(paper)
            all_chunks.extend(chunks)
        return all_chunks
    else:
        chunker = DocumentChunker()
        return chunker.chunk_documents(papers)


# Example usage
if __name__ == "__main__":
    # Sample paper
    sample_paper = {
        "id": "test123",
        "title": "Attention Is All You Need",
        "authors": ["Vaswani et al."],
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
        "published": "2017-06-12",
        "source": "arxiv",
        "url": "https://arxiv.org/abs/1706.03762",
        "categories": ["cs.CL"],
        "citations": 50000,
    }
    
    # Test chunking
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=100)
    chunks = chunker.chunk_paper(sample_paper)
    
    print(f"Created {len(chunks)} chunks")
    print(f"First chunk: {chunks[0]['content'][:100]}...")
