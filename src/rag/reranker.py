"""Document re-ranking for improved retrieval quality"""

from typing import List, Dict, Optional

from openai import OpenAI

from src.utils.config import settings
from src.utils.logger import app_logger


class Reranker:
    """Re-rank retrieved documents for better relevance"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize reranker
        
        Args:
            model: Model to use for re-ranking
        """
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model

    def rerank_with_llm(
        self,
        query: str,
        documents: List[Dict],
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Re-rank documents using LLM to assess relevance
        
        Args:
            query: User query
            documents: Retrieved documents
            top_k: Number of documents to return
            
        Returns:
            Re-ranked documents
        """
        if len(documents) == 0:
            return []
        
        try:
            # Build prompt with documents
            docs_text = ""
            for idx, doc in enumerate(documents, 1):
                content = doc.get("content", "")[:500]  # Truncate for efficiency
                docs_text += f"\n[Doc {idx}]\n{content}\n"
            
            prompt = f"""Given the query and documents below, rank the documents by relevance to the query.

Query: "{query}"

Documents:
{docs_text}

Respond with ONLY the document numbers in order of relevance (most relevant first), comma-separated.
Example: 3,1,5,2,4"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert at assessing document relevance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100,
            )
            
            ranking_text = response.choices[0].message.content.strip()
            
            # Parse ranking
            try:
                rankings = [int(r.strip()) - 1 for r in ranking_text.split(",")]
                rankings = [r for r in rankings if 0 <= r < len(documents)]
            except:
                app_logger.warning("Could not parse LLM ranking, using original order")
                rankings = list(range(len(documents)))
            
            # Reorder documents
            reranked = []
            for idx in rankings[:top_k]:
                doc = documents[idx].copy()
                doc["rerank_position"] = len(reranked) + 1
                reranked.append(doc)
            
            app_logger.info(f"Re-ranked {len(documents)} documents to {len(reranked)}")
            
            return reranked
            
        except Exception as e:
            app_logger.error(f"Error re-ranking with LLM: {e}")
            return documents[:top_k]

    def rerank_by_score(
        self,
        documents: List[Dict],
        score_key: str = "score",
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Re-rank documents by a specific score
        
        Args:
            documents: Documents to re-rank
            score_key: Key to use for scoring
            top_k: Number to return
            
        Returns:
            Re-ranked documents
        """
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get(score_key, 0),
            reverse=True
        )
        return sorted_docs[:top_k]

    def rerank_by_recency(
        self,
        documents: List[Dict],
        recency_weight: float = 0.3,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Re-rank documents considering both relevance and recency
        
        Args:
            documents: Documents to re-rank
            recency_weight: Weight for recency (0-1)
            top_k: Number to return
            
        Returns:
            Re-ranked documents
        """
        from datetime import datetime
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            published = metadata.get("published", "")
            
            # Calculate recency score (0-1)
            try:
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                days_old = (datetime.now() - pub_date).days
                # Decay over 2 years
                recency_score = max(0, 1 - (days_old / 730))
            except:
                recency_score = 0
            
            # Combine with relevance score
            relevance_score = doc.get("score", 0)
            combined_score = (
                (1 - recency_weight) * relevance_score +
                recency_weight * recency_score
            )
            
            doc["combined_score"] = combined_score
            doc["recency_score"] = recency_score
        
        # Sort by combined score
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get("combined_score", 0),
            reverse=True
        )
        
        return sorted_docs[:top_k]

    def rerank_by_citations(
        self,
        documents: List[Dict],
        citation_weight: float = 0.2,
        top_k: int = 10,
    ) -> List[Dict]:
        """
        Re-rank considering citation counts
        
        Args:
            documents: Documents to re-rank
            citation_weight: Weight for citations (0-1)
            top_k: Number to return
            
        Returns:
            Re-ranked documents
        """
        # Normalize citation counts
        max_citations = max(
            (doc.get("metadata", {}).get("citations", 0) for doc in documents),
            default=1
        )
        
        for doc in documents:
            citations = doc.get("metadata", {}).get("citations", 0)
            citation_score = citations / max_citations if max_citations > 0 else 0
            
            relevance_score = doc.get("score", 0)
            combined_score = (
                (1 - citation_weight) * relevance_score +
                citation_weight * citation_score
            )
            
            doc["combined_score"] = combined_score
            doc["citation_score"] = citation_score
        
        # Sort by combined score
        sorted_docs = sorted(
            documents,
            key=lambda x: x.get("combined_score", 0),
            reverse=True
        )
        
        return sorted_docs[:top_k]


def rerank_results(
    query: str,
    documents: List[Dict],
    top_k: int = 10,
    method: str = "hybrid",
) -> List[Dict]:
    """
    Convenience function to re-rank results
    
    Args:
        query: User query
        documents: Documents to re-rank
        top_k: Number to return
        method: Re-ranking method ('llm', 'recency', 'citations', 'hybrid')
        
    Returns:
        Re-ranked documents
    """
    reranker = Reranker()
    
    if method == "llm":
        return reranker.rerank_with_llm(query, documents, top_k)
    elif method == "recency":
        return reranker.rerank_by_recency(documents, top_k=top_k)
    elif method == "citations":
        return reranker.rerank_by_citations(documents, top_k=top_k)
    elif method == "hybrid":
        # Combine recency and citations
        docs = reranker.rerank_by_recency(documents, recency_weight=0.2, top_k=len(documents))
        return reranker.rerank_by_citations(docs, citation_weight=0.2, top_k=top_k)
    else:
        return documents[:top_k]


# Example usage
if __name__ == "__main__":
    reranker = Reranker()
    
    # Sample documents
    sample_docs = [
        {
            "id": "doc1",
            "content": "This paper discusses transformer architectures in detail...",
            "score": 0.85,
            "metadata": {"published": "2023-01-01", "citations": 100}
        },
        {
            "id": "doc2",
            "content": "Recent advances in attention mechanisms for NLP...",
            "score": 0.82,
            "metadata": {"published": "2024-06-01", "citations": 10}
        },
        {
            "id": "doc3",
            "content": "A survey of large language models and their applications...",
            "score": 0.80,
            "metadata": {"published": "2024-01-01", "citations": 50}
        },
    ]
    
    query = "latest transformer architectures"
    
    # Test different re-ranking methods
    print("Original order:")
    for i, doc in enumerate(sample_docs, 1):
        print(f"{i}. Score: {doc['score']}, Citations: {doc['metadata']['citations']}")
    
    print("\nRe-ranked by recency:")
    reranked = reranker.rerank_by_recency(sample_docs.copy())
    for i, doc in enumerate(reranked, 1):
        print(f"{i}. Combined: {doc.get('combined_score', 0):.3f}, Recency: {doc.get('recency_score', 0):.3f}")
    
    print("\nRe-ranked by citations:")
    reranked = reranker.rerank_by_citations(sample_docs.copy())
    for i, doc in enumerate(reranked, 1):
        print(f"{i}. Combined: {doc.get('combined_score', 0):.3f}, Citations: {doc['metadata']['citations']}")
