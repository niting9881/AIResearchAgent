"""Query rewriting and enhancement for better retrieval"""

from typing import List, Optional

from openai import OpenAI

from src.utils.config import settings
from src.utils.logger import app_logger


class QueryRewriter:
    """Rewrite and enhance queries for better retrieval"""

    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize query rewriter
        
        Args:
            model: OpenAI model for query rewriting
        """
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model

    def rewrite_query(self, query: str) -> str:
        """
        Rewrite query to be more specific and retrieval-friendly
        
        Args:
            query: Original user query
            
        Returns:
            Rewritten query
        """
        if not settings.enable_query_rewriting:
            return query
        
        try:
            prompt = f"""You are an expert at reformulating search queries for academic paper retrieval.

Original query: "{query}"

Rewrite this query to be more specific, detailed, and better suited for semantic search in a database of Large Language Model research papers. Include relevant technical terms and concepts.

Return only the rewritten query, nothing else."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a search query optimization expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
            )
            
            rewritten = response.choices[0].message.content.strip()
            
            app_logger.info(f"Original: '{query}'")
            app_logger.info(f"Rewritten: '{rewritten}'")
            
            return rewritten
            
        except Exception as e:
            app_logger.error(f"Error rewriting query: {e}")
            return query

    def generate_sub_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """
        Generate multiple sub-queries from a complex query
        
        Args:
            query: Original query
            num_queries: Number of sub-queries to generate
            
        Returns:
            List of sub-queries
        """
        try:
            prompt = f"""Break down this complex query into {num_queries} specific sub-queries that can be answered independently.

Original query: "{query}"

Generate {num_queries} focused sub-queries, one per line. Each should address a specific aspect of the original question."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a query decomposition expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300,
            )
            
            content = response.choices[0].message.content.strip()
            sub_queries = [q.strip().strip('123.-') for q in content.split('\n') if q.strip()]
            
            app_logger.info(f"Generated {len(sub_queries)} sub-queries from: '{query}'")
            
            return sub_queries[:num_queries]
            
        except Exception as e:
            app_logger.error(f"Error generating sub-queries: {e}")
            return [query]

    def expand_query(self, query: str) -> str:
        """
        Expand query with synonyms and related terms
        
        Args:
            query: Original query
            
        Returns:
            Expanded query
        """
        try:
            prompt = f"""Add relevant synonyms and related technical terms to this query to improve semantic search.

Original query: "{query}"

Return an expanded version that includes synonyms and related concepts, maintaining the original meaning. Keep it concise."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a semantic search expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
            )
            
            expanded = response.choices[0].message.content.strip()
            
            app_logger.info(f"Expanded query: '{expanded}'")
            
            return expanded
            
        except Exception as e:
            app_logger.error(f"Error expanding query: {e}")
            return query

    def correct_spelling(self, query: str) -> str:
        """
        Correct spelling errors in query
        
        Args:
            query: Query with potential spelling errors
            
        Returns:
            Corrected query
        """
        try:
            prompt = f"""Correct any spelling errors in this query. If there are no errors, return it unchanged.

Query: "{query}"

Return only the corrected query, nothing else."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a spelling correction expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150,
            )
            
            corrected = response.choices[0].message.content.strip()
            
            if corrected != query:
                app_logger.info(f"Corrected: '{query}' -> '{corrected}'")
            
            return corrected
            
        except Exception as e:
            app_logger.error(f"Error correcting spelling: {e}")
            return query

    def extract_intent(self, query: str) -> dict:
        """
        Extract user intent from query
        
        Args:
            query: User query
            
        Returns:
            Dictionary with intent information
        """
        try:
            prompt = f"""Analyze this query and extract:
1. Main intent (research_question, definition, comparison, tutorial, latest_news)
2. Key entities (specific models, techniques, papers mentioned)
3. Time scope (recent, historical, specific year, or none)

Query: "{query}"

Respond in this exact format:
Intent: [one of the intents above]
Entities: [comma-separated list or "none"]
Time Scope: [time scope or "none"]"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a query intent analyzer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=150,
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse response
            intent_data = {"intent": "research_question", "entities": [], "time_scope": None}
            
            for line in content.split('\n'):
                if line.startswith("Intent:"):
                    intent_data["intent"] = line.split(":", 1)[1].strip()
                elif line.startswith("Entities:"):
                    entities = line.split(":", 1)[1].strip()
                    if entities.lower() != "none":
                        intent_data["entities"] = [e.strip() for e in entities.split(",")]
                elif line.startswith("Time Scope:"):
                    time_scope = line.split(":", 1)[1].strip()
                    if time_scope.lower() != "none":
                        intent_data["time_scope"] = time_scope
            
            app_logger.info(f"Extracted intent: {intent_data}")
            
            return intent_data
            
        except Exception as e:
            app_logger.error(f"Error extracting intent: {e}")
            return {"intent": "research_question", "entities": [], "time_scope": None}


class QueryProcessor:
    """Complete query processing pipeline"""

    def __init__(self):
        self.rewriter = QueryRewriter()

    def process_query(
        self,
        query: str,
        correct_spelling: bool = True,
        rewrite: bool = True,
        extract_intent: bool = True,
    ) -> dict:
        """
        Process query through complete pipeline
        
        Args:
            query: Original query
            correct_spelling: Whether to correct spelling
            rewrite: Whether to rewrite query
            extract_intent: Whether to extract intent
            
        Returns:
            Dictionary with processed query and metadata
        """
        result = {
            "original_query": query,
            "processed_query": query,
            "intent": None,
            "sub_queries": [],
        }
        
        # Spell correction
        if correct_spelling:
            query = self.rewriter.correct_spelling(query)
        
        # Query rewriting
        if rewrite:
            query = self.rewriter.rewrite_query(query)
        
        result["processed_query"] = query
        
        # Intent extraction
        if extract_intent:
            result["intent"] = self.rewriter.extract_intent(query)
        
        return result


# Example usage
if __name__ == "__main__":
    rewriter = QueryRewriter()
    
    # Test queries
    test_queries = [
        "what is attention mechanism?",
        "latest develpments in LLMs",  # has spelling error
        "Compare GPT-4 and Claude in terms of reasoning capabilities",
    ]
    
    for query in test_queries:
        print(f"\nOriginal: {query}")
        
        # Correct spelling
        corrected = rewriter.correct_spelling(query)
        print(f"Corrected: {corrected}")
        
        # Rewrite
        rewritten = rewriter.rewrite_query(corrected)
        print(f"Rewritten: {rewritten}")
        
        # Extract intent
        intent = rewriter.extract_intent(corrected)
        print(f"Intent: {intent}")
        
        print("-" * 80)
