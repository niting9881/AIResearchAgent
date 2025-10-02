"""Retrieval strategies for RAG"""

from typing import Dict, List, Optional
from enum import Enum

from src.processing.embeddings import EmbeddingGenerator
from src.vector_db.qdrant_client import QdrantManager
from src.utils.config import settings
from src.utils.logger import app_logger


class SearchStrategy(Enum):
    """Available search strategies"""
    VECTOR = "vector"
    HYBRID = "hybrid"
    KEYWORD = "keyword"


class HybridRetriever:
    """Advanced retriever with multiple search strategies"""

    def __init__(
        self,
        strategy: SearchStrategy = SearchStrategy.HYBRID,
        top_k: int = None,
    ):
        """
        Initialize retriever
        
        Args:
            strategy: Search strategy to use
            top_k: Number of results to return
        """
        self.strategy = strategy
        self.top_k = top_k or settings.top_k_retrieval
        
        # Initialize components
        self.embedding_generator = EmbeddingGenerator()
        self.vector_db = QdrantManager()
        
        app_logger.info(f"Initialized retriever with strategy: {self.strategy.value}")

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict] = None,
        rerank: bool = True,
    ) -> List[Dict]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: User query
            top_k: Number of results (overrides default)
            filters: Optional filters (e.g., year, source)
            rerank: Whether to rerank results
            
        Returns:
            List of retrieved documents with scores
        """
        top_k = top_k or self.top_k
        
        app_logger.info(f"Retrieving documents for query: '{query[:100]}...'")
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_embedding(query)
        
        # Retrieve based on strategy
        if self.strategy == SearchStrategy.VECTOR:
            results = self._vector_search(query_embedding, top_k, filters)
        elif self.strategy == SearchStrategy.HYBRID:
            results = self._hybrid_search(query_embedding, query, top_k, filters)
        else:
            results = self._keyword_search(query, top_k, filters)
        
        # Rerank if enabled
        if rerank and settings.enable_reranking:
            from src.rag.reranker import rerank_results
            results = rerank_results(query, results, top_k)
        
        app_logger.info(f"Retrieved {len(results)} documents")
        
        return results

    def _vector_search(
        self,
        query_embedding: List[float],
        top_k: int,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """Vector similarity search"""
        return self.vector_db.search(
            query_vector=query_embedding,
            limit=top_k,
            filters=filters,
            score_threshold=settings.similarity_threshold,
        )

    def _hybrid_search(
        self,
        query_embedding: List[float],
        query_text: str,
        top_k: int,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """Hybrid search combining vector and keyword search"""
        return self.vector_db.hybrid_search(
            query_vector=query_embedding,
            query_text=query_text,
            limit=top_k,
        )

    def _keyword_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict] = None,
    ) -> List[Dict]:
        """Keyword-based search (BM25-like)"""
        # Note: This requires text indexing in Qdrant
        # For now, falling back to vector search with text filtering
        query_embedding = self.embedding_generator.generate_embedding(query)
        return self._vector_search(query_embedding, top_k, filters)

    def batch_retrieve(
        self,
        queries: List[str],
        top_k: Optional[int] = None,
    ) -> List[List[Dict]]:
        """
        Retrieve documents for multiple queries
        
        Args:
            queries: List of queries
            top_k: Number of results per query
            
        Returns:
            List of result lists
        """
        all_results = []
        
        for query in queries:
            results = self.retrieve(query, top_k=top_k)
            all_results.append(results)
        
        return all_results


class ContextBuilder:
    """Build context for LLM from retrieved documents"""

    def __init__(self, max_context_length: int = 4000):
        """
        Initialize context builder
        
        Args:
            max_context_length: Maximum context length in characters
        """
        self.max_context_length = max_context_length

    def build_context(
        self,
        query: str,
        retrieved_docs: List[Dict],
        include_metadata: bool = True,
    ) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            query: User query
            retrieved_docs: Retrieved documents
            include_metadata: Whether to include metadata
            
        Returns:
            Formatted context string
        """
        context_parts = []
        current_length = 0
        
        for idx, doc in enumerate(retrieved_docs, 1):
            # Format document
            doc_text = f"\n[Document {idx}]"
            
            if include_metadata:
                metadata = doc.get("metadata", {})
                title = metadata.get("title", "Unknown")
                authors = metadata.get("authors", [])
                year = metadata.get("published", "")[:4] if metadata.get("published") else "Unknown"
                
                doc_text += f"\nTitle: {title}"
                doc_text += f"\nAuthors: {', '.join(authors[:3])}"
                doc_text += f"\nYear: {year}"
                doc_text += f"\nRelevance Score: {doc.get('score', 0):.3f}"
            
            doc_text += f"\nContent: {doc.get('content', '')}\n"
            
            # Check length
            if current_length + len(doc_text) > self.max_context_length:
                app_logger.info(f"Reached max context length at document {idx}")
                break
            
            context_parts.append(doc_text)
            current_length += len(doc_text)
        
        context = "\n".join(context_parts)
        
        app_logger.info(f"Built context with {len(context_parts)} documents ({current_length} chars)")
        
        return context

    def build_context_with_citations(
        self,
        query: str,
        retrieved_docs: List[Dict],
    ) -> tuple[str, List[Dict]]:
        """
        Build context with citation tracking
        
        Args:
            query: User query
            retrieved_docs: Retrieved documents
            
        Returns:
            Tuple of (context_string, citations_list)
        """
        citations = []
        context_parts = []
        
        for idx, doc in enumerate(retrieved_docs, 1):
            metadata = doc.get("metadata", {})
            
            # Add to citations
            citation = {
                "id": idx,
                "title": metadata.get("title", "Unknown"),
                "authors": metadata.get("authors", []),
                "year": metadata.get("published", "")[:4] if metadata.get("published") else "Unknown",
                "url": metadata.get("url", ""),
                "score": doc.get("score", 0),
            }
            citations.append(citation)
            
            # Build context with citation markers
            doc_text = f"\n[{idx}] {doc.get('content', '')}"
            context_parts.append(doc_text)
        
        context = "\n".join(context_parts)
        
        return context, citations


def reciprocal_rank_fusion(
    result_lists: List[List[Dict]],
    k: int = 60,
) -> List[Dict]:
    """
    Combine multiple result lists using Reciprocal Rank Fusion
    
    Args:
        result_lists: List of result lists from different retrievers
        k: Constant for RRF (default: 60)
        
    Returns:
        Fused and re-ranked results
    """
    # Collect all unique documents
    doc_scores = {}
    
    for results in result_lists:
        for rank, doc in enumerate(results, 1):
            doc_id = doc.get("id", doc.get("chunk_id"))
            
            # Calculate RRF score
            rrf_score = 1 / (k + rank)
            
            if doc_id in doc_scores:
                doc_scores[doc_id]["score"] += rrf_score
            else:
                doc_scores[doc_id] = {
                    **doc,
                    "score": rrf_score,
                }
    
    # Sort by combined score
    fused_results = sorted(
        doc_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )
    
    return fused_results


# Example usage
if __name__ == "__main__":
    # Initialize retriever
    retriever = HybridRetriever(strategy=SearchStrategy.HYBRID)
    
    # Sample query
    query = "What are the latest advances in transformer architectures?"
    
    # Retrieve documents
    results = retriever.retrieve(query, top_k=5)
    
    print(f"Retrieved {len(results)} documents:")
    for i, result in enumerate(results, 1):
        print(f"{i}. Score: {result['score']:.3f}")
        print(f"   Content: {result['content'][:100]}...")
        print()
    
    # Build context
    builder = ContextBuilder()
    context = builder.build_context(query, results)
    print(f"\nContext length: {len(context)} characters")
