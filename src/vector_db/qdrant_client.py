"""Qdrant vector database client"""

from typing import Dict, List, Optional, Union
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    SearchRequest,
)

from src.utils.config import settings
from src.utils.logger import app_logger


class QdrantManager:
    """Manage Qdrant vector database operations"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        collection_name: Optional[str] = None,
    ):
        """
        Initialize Qdrant client
        
        Args:
            host: Qdrant host
            port: Qdrant port
            collection_name: Name of the collection
        """
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.collection_name = collection_name or settings.qdrant_collection_name
        
        # Initialize client
        self.client = QdrantClient(
            host=self.host,
            port=self.port,
            api_key=settings.qdrant_api_key,
        )
        
        app_logger.info(f"Connected to Qdrant at {self.host}:{self.port}")

    def create_collection_if_not_exists(self, vector_size: int = 1536):
        """
        Create collection if it doesn't exist
        
        Args:
            vector_size: Size of embedding vectors
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [col.name for col in collections]
            
            if self.collection_name in collection_names:
                app_logger.info(f"Collection '{self.collection_name}' already exists")
                return
            
            # Create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )
            
            app_logger.info(f"Created collection '{self.collection_name}'")
            
        except Exception as e:
            app_logger.error(f"Error creating collection: {e}")
            raise

    def index_documents(self, chunks: List[Dict], embeddings: Optional[List[List[float]]] = None):
        """
        Index document chunks into Qdrant
        
        Args:
            chunks: List of chunk dictionaries
            embeddings: List of embedding vectors (if not in chunks)
        """
        try:
            points = []
            
            for idx, chunk in enumerate(chunks):
                # Get embedding
                if embeddings:
                    embedding = embeddings[idx]
                elif "embedding" in chunk:
                    embedding = chunk["embedding"]
                else:
                    app_logger.warning(f"No embedding found for chunk {chunk.get('id', idx)}")
                    continue
                
                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),  # Generate unique ID
                    vector=embedding,
                    payload={
                        "chunk_id": chunk.get("id"),
                        "paper_id": chunk.get("paper_id"),
                        "content": chunk.get("content", ""),
                        "chunk_index": chunk.get("chunk_index", 0),
                        "metadata": chunk.get("metadata", {}),
                    }
                )
                points.append(point)
            
            # Upload points in batches
            batch_size = 100
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch
                )
                app_logger.info(f"Indexed batch {i // batch_size + 1}/{(len(points) + batch_size - 1) // batch_size}")
            
            app_logger.info(f"Successfully indexed {len(points)} documents")
            
        except Exception as e:
            app_logger.error(f"Error indexing documents: {e}")
            raise

    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None,
    ) -> List[Dict]:
        """
        Search for similar documents
        
        Args:
            query_vector: Query embedding vector
            limit: Number of results to return
            filters: Optional filters (e.g., {"source": "arxiv"})
            score_threshold: Minimum similarity score
            
        Returns:
            List of search results with scores
        """
        try:
            # Build filter if provided
            search_filter = None
            if filters:
                search_filter = self._build_filter(filters)
            
            # Perform search
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=search_filter,
                score_threshold=score_threshold,
            )
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "id": result.payload.get("chunk_id"),
                    "paper_id": result.payload.get("paper_id"),
                    "content": result.payload.get("content"),
                    "metadata": result.payload.get("metadata", {}),
                    "score": result.score,
                })
            
            app_logger.info(f"Found {len(formatted_results)} results")
            
            return formatted_results
            
        except Exception as e:
            app_logger.error(f"Error searching: {e}")
            raise

    def hybrid_search(
        self,
        query_vector: List[float],
        query_text: str,
        limit: int = 10,
        vector_weight: float = 0.7,
    ) -> List[Dict]:
        """
        Perform hybrid search (vector + text)
        
        Args:
            query_vector: Query embedding vector
            query_text: Query text for keyword search
            limit: Number of results
            vector_weight: Weight for vector search (0-1)
            
        Returns:
            List of search results
        """
        # Note: Qdrant hybrid search requires text index
        # This is a simplified implementation
        # For production, implement proper hybrid search with text indexing
        
        # For now, use vector search with text filtering
        results = self.search(
            query_vector=query_vector,
            limit=limit * 2,  # Get more results for filtering
        )
        
        # Simple text relevance scoring
        text_weight = 1 - vector_weight
        query_terms = set(query_text.lower().split())
        
        for result in results:
            content_terms = set(result["content"].lower().split())
            text_overlap = len(query_terms & content_terms) / len(query_terms) if query_terms else 0
            
            # Combine scores
            result["combined_score"] = (
                vector_weight * result["score"] +
                text_weight * text_overlap
            )
        
        # Re-rank by combined score
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return results[:limit]

    def _build_filter(self, filters: Dict) -> Filter:
        """Build Qdrant filter from dictionary"""
        conditions = []
        
        for key, value in filters.items():
            if isinstance(value, (str, int, bool)):
                conditions.append(
                    FieldCondition(
                        key=f"metadata.{key}",
                        match=MatchValue(value=value)
                    )
                )
            elif isinstance(value, dict) and "gte" in value:
                conditions.append(
                    FieldCondition(
                        key=f"metadata.{key}",
                        range=Range(gte=value["gte"])
                    )
                )
        
        return Filter(must=conditions) if conditions else None

    def get_collection_info(self) -> Dict:
        """Get information about the collection"""
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
            }
        except Exception as e:
            app_logger.error(f"Error getting collection info: {e}")
            return {}

    def delete_collection(self):
        """Delete the collection"""
        try:
            self.client.delete_collection(self.collection_name)
            app_logger.info(f"Deleted collection '{self.collection_name}'")
        except Exception as e:
            app_logger.error(f"Error deleting collection: {e}")
            raise


# Example usage
if __name__ == "__main__":
    # Initialize manager
    manager = QdrantManager()
    
    # Create collection
    manager.create_collection_if_not_exists()
    
    # Sample data
    sample_chunks = [
        {
            "id": "chunk1",
            "paper_id": "paper1",
            "content": "Large language models are transformer-based architectures.",
            "embedding": [0.1] * 1536,  # Dummy embedding
            "metadata": {"title": "LLM Paper", "source": "arxiv"}
        }
    ]
    
    # Index documents
    manager.index_documents(sample_chunks)
    
    # Get collection info
    info = manager.get_collection_info()
    print(f"Collection info: {info}")
