"""Complete RAG pipeline integrating all components"""

from typing import Dict, List, Optional
import time

from src.rag.retriever import HybridRetriever, ContextBuilder, SearchStrategy
from src.rag.query_rewriter import QueryProcessor
from src.llm.openai_client import OpenAIClient
from src.llm.prompt_templates import PromptTemplates
from src.utils.config import settings
from src.utils.logger import app_logger


class RAGPipeline:
    """Complete RAG pipeline from query to response"""

    def __init__(
        self,
        search_strategy: SearchStrategy = SearchStrategy.HYBRID,
        enable_query_rewriting: bool = True,
        enable_reranking: bool = True,
    ):
        """
        Initialize RAG pipeline
        
        Args:
            search_strategy: Retrieval strategy
            enable_query_rewriting: Whether to rewrite queries
            enable_reranking: Whether to rerank results
        """
        self.retriever = HybridRetriever(strategy=search_strategy)
        self.query_processor = QueryProcessor() if enable_query_rewriting else None
        self.context_builder = ContextBuilder()
        self.llm_client = OpenAIClient()
        
        self.enable_reranking = enable_reranking
        
        app_logger.info("Initialized RAG pipeline")

    def query(
        self,
        user_query: str,
        top_k: int = None,
        filters: Optional[Dict] = None,
        prompt_style: str = "balanced",
        temperature: float = 0.7,
    ) -> Dict:
        """
        Execute complete RAG pipeline
        
        Args:
            user_query: User's question
            top_k: Number of documents to retrieve
            filters: Optional filters for retrieval
            prompt_style: Style of system prompt
            temperature: LLM temperature
            
        Returns:
            Dictionary with answer and metadata
        """
        start_time = time.time()
        
        app_logger.info(f"Processing query: '{user_query}'")
        
        result = {
            "query": user_query,
            "processed_query": user_query,
            "intent": None,
            "retrieved_docs": [],
            "context": "",
            "answer": "",
            "citations": [],
            "timing": {},
            "metadata": {},
        }
        
        try:
            # Step 1: Query Processing
            query_start = time.time()
            
            if self.query_processor and settings.enable_query_rewriting:
                query_data = self.query_processor.process_query(user_query)
                processed_query = query_data["processed_query"]
                result["intent"] = query_data.get("intent")
                result["processed_query"] = processed_query
            else:
                processed_query = user_query
            
            result["timing"]["query_processing"] = time.time() - query_start
            
            # Step 2: Retrieval
            retrieval_start = time.time()
            
            retrieved_docs = self.retriever.retrieve(
                query=processed_query,
                top_k=top_k,
                filters=filters,
                rerank=self.enable_reranking,
            )
            
            result["retrieved_docs"] = retrieved_docs
            result["timing"]["retrieval"] = time.time() - retrieval_start
            
            # Step 3: Context Building
            context_start = time.time()
            
            # Determine prompt style from intent
            if result["intent"]:
                intent_type = result["intent"].get("intent", "research_question")
            else:
                intent_type = "research_question"
            
            context, citations = self.context_builder.build_context_with_citations(
                user_query,
                retrieved_docs,
            )
            
            result["context"] = context
            result["citations"] = citations
            result["timing"]["context_building"] = time.time() - context_start
            
            # Step 4: LLM Generation
            generation_start = time.time()
            
            system_prompt = PromptTemplates.get_system_prompt(prompt_style)
            user_prompt = PromptTemplates.get_prompt_for_intent(
                user_query,
                context,
                intent_type,
            )
            
            llm_response = self.llm_client.generate_response(
                query=user_prompt,
                context="",  # Context already in prompt
                system_prompt=system_prompt,
                temperature=temperature,
            )
            
            result["answer"] = llm_response["answer"]
            result["metadata"] = {
                "model": llm_response["model"],
                "tokens_used": llm_response["tokens_used"],
                "prompt_tokens": llm_response["prompt_tokens"],
                "completion_tokens": llm_response["completion_tokens"],
            }
            
            result["timing"]["generation"] = llm_response["generation_time"]
            
            # Total time
            result["timing"]["total"] = time.time() - start_time
            
            app_logger.info(f"Pipeline completed in {result['timing']['total']:.2f}s")
            app_logger.info(f"  - Query processing: {result['timing']['query_processing']:.2f}s")
            app_logger.info(f"  - Retrieval: {result['timing']['retrieval']:.2f}s")
            app_logger.info(f"  - Context building: {result['timing']['context_building']:.2f}s")
            app_logger.info(f"  - Generation: {result['timing']['generation']:.2f}s")
            
            return result
            
        except Exception as e:
            app_logger.error(f"Error in RAG pipeline: {e}")
            result["answer"] = "Sorry, I encountered an error processing your query. Please try again."
            result["error"] = str(e)
            return result

    def batch_query(
        self,
        queries: List[str],
        top_k: int = None,
    ) -> List[Dict]:
        """
        Process multiple queries
        
        Args:
            queries: List of user queries
            top_k: Number of documents per query
            
        Returns:
            List of results
        """
        results = []
        
        for query in queries:
            result = self.query(query, top_k=top_k)
            results.append(result)
        
        return results

    def query_streaming(
        self,
        user_query: str,
        top_k: int = None,
        filters: Optional[Dict] = None,
    ):
        """
        Execute RAG pipeline with streaming response
        
        Args:
            user_query: User's question
            top_k: Number of documents to retrieve
            filters: Optional filters
            
        Yields:
            Response chunks and metadata
        """
        # Retrieve and build context (non-streaming)
        if self.query_processor and settings.enable_query_rewriting:
            query_data = self.query_processor.process_query(user_query)
            processed_query = query_data["processed_query"]
        else:
            processed_query = user_query
        
        retrieved_docs = self.retriever.retrieve(
            query=processed_query,
            top_k=top_k,
            filters=filters,
            rerank=self.enable_reranking,
        )
        
        context, citations = self.context_builder.build_context_with_citations(
            user_query,
            retrieved_docs,
        )
        
        # Yield metadata first
        yield {
            "type": "metadata",
            "retrieved_docs": len(retrieved_docs),
            "citations": citations,
        }
        
        # Stream the response
        system_prompt = PromptTemplates.get_system_prompt("balanced")
        
        for chunk in self.llm_client.generate_with_streaming(
            user_query,
            context,
            system_prompt,
        ):
            yield {
                "type": "chunk",
                "content": chunk,
            }


# Example usage
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = RAGPipeline(
        search_strategy=SearchStrategy.HYBRID,
        enable_query_rewriting=True,
        enable_reranking=True,
    )
    
    # Sample query
    query = "What are the key innovations in transformer architectures?"
    
    # Execute pipeline
    print(f"Query: {query}\n")
    
    result = pipeline.query(query, top_k=5)
    
    print(f"Processed Query: {result['processed_query']}")
    print(f"Retrieved {len(result['retrieved_docs'])} documents")
    print(f"\nAnswer:\n{result['answer']}")
    print(f"\nCitations:")
    for citation in result['citations'][:3]:
        print(f"  [{citation['id']}] {citation['title']} ({citation['year']})")
    
    print(f"\nTiming:")
    for step, duration in result['timing'].items():
        print(f"  {step}: {duration:.2f}s")
    
    print(f"\nTokens used: {result['metadata']['tokens_used']}")
