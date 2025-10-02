"""OpenAI LLM client for response generation"""

from typing import Dict, List, Optional
import time

from openai import OpenAI

from src.utils.config import settings
from src.utils.logger import app_logger
from src.utils.helpers import count_tokens


class OpenAIClient:
    """Client for OpenAI LLM"""

    def __init__(self, model: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            model: Model name (defaults to config)
        """
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.openai_model

    def generate_response(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> Dict:
        """
        Generate response using OpenAI
        
        Args:
            query: User query
            context: Retrieved context
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with response and metadata
        """
        start_time = time.time()
        
        try:
            # Build messages
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # User message with context
            user_message = f"""Context from research papers:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above. Include citations to specific papers when relevant."""
            
            messages.append({"role": "user", "content": user_message})
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            
            # Extract response
            answer = response.choices[0].message.content
            
            # Calculate metrics
            generation_time = time.time() - start_time
            
            result = {
                "answer": answer,
                "model": self.model,
                "tokens_used": response.usage.total_tokens,
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "generation_time": generation_time,
                "finish_reason": response.choices[0].finish_reason,
            }
            
            app_logger.info(f"Generated response in {generation_time:.2f}s using {result['tokens_used']} tokens")
            
            return result
            
        except Exception as e:
            app_logger.error(f"Error generating response: {e}")
            raise

    def generate_with_streaming(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
    ):
        """
        Generate response with streaming
        
        Args:
            query: User query
            context: Retrieved context
            system_prompt: System prompt (optional)
            
        Yields:
            Response chunks as they arrive
        """
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            user_message = f"""Context from research papers:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above."""
            
            messages.append({"role": "user", "content": user_message})
            
            # Stream response
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            app_logger.error(f"Error in streaming: {e}")
            raise


# Example usage
if __name__ == "__main__":
    client = OpenAIClient()
    
    # Sample context and query
    context = """
    [Document 1]
    Title: Attention Is All You Need
    The Transformer architecture uses self-attention mechanisms to process sequences...
    
    [Document 2]
    Title: BERT: Pre-training of Deep Bidirectional Transformers
    BERT uses masked language modeling for pre-training...
    """
    
    query = "What is the transformer architecture?"
    
    # Generate response
    result = client.generate_response(query, context)
    
    print(f"Answer: {result['answer']}")
    print(f"Tokens used: {result['tokens_used']}")
    print(f"Time: {result['generation_time']:.2f}s")
