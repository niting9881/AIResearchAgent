"""Embedding generation using OpenAI API"""

from typing import List, Dict, Optional
import time

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.utils.config import settings
from src.utils.logger import app_logger


class EmbeddingGenerator:
    """Generate embeddings using OpenAI API"""

    def __init__(self, model: Optional[str] = None, batch_size: int = 100):
        """
        Initialize embedding generator
        
        Args:
            model: OpenAI embedding model name
            batch_size: Number of texts to embed in one batch
        """
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.openai_embedding_model
        self.batch_size = batch_size
        self.embedding_cache = {}  # Simple cache for deduplication

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            # Check cache
            if text in self.embedding_cache:
                app_logger.debug("Using cached embedding")
                return self.embedding_cache[text]
            
            # Clean and truncate text if needed
            text = text.replace("\n", " ").strip()
            
            # Generate embedding
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            
            # Cache the result
            self.embedding_cache[text] = embedding
            
            return embedding
            
        except Exception as e:
            app_logger.error(f"Error generating embedding: {e}")
            raise

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            # Clean texts
            cleaned_texts = [text.replace("\n", " ").strip() for text in texts]
            
            # Generate embeddings
            response = self.client.embeddings.create(
                model=self.model,
                input=cleaned_texts
            )
            
            embeddings = [item.embedding for item in response.data]
            
            app_logger.info(f"Generated {len(embeddings)} embeddings")
            
            return embeddings
            
        except Exception as e:
            app_logger.error(f"Error generating batch embeddings: {e}")
            raise

    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Generate embeddings for document chunks
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of chunks with embeddings added
        """
        app_logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        embedded_chunks = []
        
        # Process in batches
        for i in range(0, len(chunks), self.batch_size):
            batch = chunks[i:i + self.batch_size]
            batch_texts = [chunk["content"] for chunk in batch]
            
            try:
                # Generate embeddings for batch
                embeddings = self.generate_embeddings_batch(batch_texts)
                
                # Add embeddings to chunks
                for chunk, embedding in zip(batch, embeddings):
                    chunk["embedding"] = embedding
                    embedded_chunks.append(chunk)
                
                app_logger.info(f"Processed batch {i // self.batch_size + 1}/{(len(chunks) + self.batch_size - 1) // self.batch_size}")
                
                # Rate limiting - be nice to the API
                if i + self.batch_size < len(chunks):
                    time.sleep(0.5)
                    
            except Exception as e:
                app_logger.error(f"Error processing batch {i // self.batch_size + 1}: {e}")
                # Continue with next batch
                continue
        
        app_logger.info(f"Successfully generated embeddings for {len(embedded_chunks)}/{len(chunks)} chunks")
        
        return embedded_chunks

    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings for the current model
        
        Returns:
            Embedding dimension
        """
        if "text-embedding-3-small" in self.model:
            return 1536
        elif "text-embedding-3-large" in self.model:
            return 3072
        elif "text-embedding-ada-002" in self.model:
            return 1536
        else:
            # Default, will be overridden by actual embedding
            return 1536


def generate_embeddings(chunks: List[Dict], model: Optional[str] = None) -> List[Dict]:
    """
    Convenience function to generate embeddings for chunks
    
    Args:
        chunks: List of chunk dictionaries
        model: OpenAI embedding model (optional)
        
    Returns:
        List of chunks with embeddings
    """
    generator = EmbeddingGenerator(model=model)
    return generator.embed_chunks(chunks)


def calculate_embedding_cost(num_tokens: int, model: str = "text-embedding-3-small") -> float:
    """
    Calculate cost for embedding generation
    
    Args:
        num_tokens: Number of tokens to embed
        model: Model name
        
    Returns:
        Estimated cost in USD
    """
    # Pricing as of 2024 (per 1M tokens)
    pricing = {
        "text-embedding-3-small": 0.02,  # $0.02 per 1M tokens
        "text-embedding-3-large": 0.13,  # $0.13 per 1M tokens
        "text-embedding-ada-002": 0.10,  # $0.10 per 1M tokens
    }
    
    price_per_million = pricing.get(model, 0.02)
    cost = (num_tokens / 1_000_000) * price_per_million
    
    return cost


# Example usage
if __name__ == "__main__":
    # Sample chunks
    sample_chunks = [
        {
            "id": "chunk1",
            "paper_id": "paper1",
            "content": "This is a sample text about large language models.",
            "metadata": {"title": "Sample Paper"}
        },
        {
            "id": "chunk2",
            "paper_id": "paper1",
            "content": "Attention mechanisms are key to transformer architectures.",
            "metadata": {"title": "Sample Paper"}
        }
    ]
    
    # Generate embeddings
    generator = EmbeddingGenerator()
    embedded_chunks = generator.embed_chunks(sample_chunks)
    
    print(f"Generated embeddings for {len(embedded_chunks)} chunks")
    print(f"Embedding dimension: {len(embedded_chunks[0]['embedding'])}")
    
    # Calculate cost
    total_tokens = sum(chunk.get("token_count", 100) for chunk in sample_chunks)
    cost = calculate_embedding_cost(total_tokens)
    print(f"Estimated cost: ${cost:.4f}")
