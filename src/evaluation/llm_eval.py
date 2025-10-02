"""LLM response evaluation metrics"""

from typing import Dict, List, Optional
import re

from openai import OpenAI

from src.utils.config import settings
from src.utils.logger import app_logger


class LLMEvaluator:
    """Evaluate LLM response quality"""

    def __init__(self, model: str = "gpt-4o"):
        """
        Initialize LLM evaluator
        
        Args:
            model: Model to use for evaluation (LLM-as-judge)
        """
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model

    def evaluate_relevance(self, query: str, response: str, context: str) -> float:
        """
        Evaluate if response is relevant to the query
        
        Args:
            query: User query
            response: LLM response
            context: Retrieved context
            
        Returns:
            Relevance score (0-1)
        """
        prompt = f"""Evaluate the relevance of the answer to the question on a scale of 0-1.

Question: {query}

Answer: {response}

Rate the relevance (0 = completely irrelevant, 1 = highly relevant).
Respond with ONLY a number between 0 and 1."""

        try:
            result = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of question-answer relevance."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10,
            )
            
            score_text = result.choices[0].message.content.strip()
            score = float(re.search(r'0?\.\d+|[01]', score_text).group())
            
            return max(0, min(1, score))
            
        except Exception as e:
            app_logger.error(f"Error evaluating relevance: {e}")
            return 0.5

    def evaluate_coherence(self, response: str) -> float:
        """
        Evaluate response coherence and structure
        
        Args:
            response: LLM response
            
        Returns:
            Coherence score (0-1)
        """
        prompt = f"""Evaluate the coherence and structure of this text on a scale of 0-1.

Text: {response}

Consider:
- Logical flow of ideas
- Clear structure
- Grammatical correctness
- Readability

Rate the coherence (0 = incoherent, 1 = perfectly coherent).
Respond with ONLY a number between 0 and 1."""

        try:
            result = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of text coherence."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10,
            )
            
            score_text = result.choices[0].message.content.strip()
            score = float(re.search(r'0?\.\d+|[01]', score_text).group())
            
            return max(0, min(1, score))
            
        except Exception as e:
            app_logger.error(f"Error evaluating coherence: {e}")
            return 0.5

    def evaluate_factuality(self, response: str, context: str) -> float:
        """
        Evaluate if response is factually grounded in context
        
        Args:
            response: LLM response
            context: Retrieved context
            
        Returns:
            Factuality score (0-1)
        """
        prompt = f"""Evaluate if the answer is factually grounded in the provided context.

Context: {context[:2000]}...

Answer: {response}

Rate the factual accuracy (0 = not grounded, contains hallucinations, 1 = fully grounded in context).
Respond with ONLY a number between 0 and 1."""

        try:
            result = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of factual accuracy."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10,
            )
            
            score_text = result.choices[0].message.content.strip()
            score = float(re.search(r'0?\.\d+|[01]', score_text).group())
            
            return max(0, min(1, score))
            
        except Exception as e:
            app_logger.error(f"Error evaluating factuality: {e}")
            return 0.5

    def evaluate_completeness(self, query: str, response: str) -> float:
        """
        Evaluate if response fully answers the question
        
        Args:
            query: User query
            response: LLM response
            
        Returns:
            Completeness score (0-1)
        """
        prompt = f"""Evaluate if the answer completely addresses all aspects of the question.

Question: {query}

Answer: {response}

Rate the completeness (0 = incomplete, 1 = fully complete).
Respond with ONLY a number between 0 and 1."""

        try:
            result = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert evaluator of answer completeness."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=10,
            )
            
            score_text = result.choices[0].message.content.strip()
            score = float(re.search(r'0?\.\d+|[01]', score_text).group())
            
            return max(0, min(1, score))
            
        except Exception as e:
            app_logger.error(f"Error evaluating completeness: {e}")
            return 0.5

    def evaluate_all(
        self,
        query: str,
        response: str,
        context: str,
    ) -> Dict[str, float]:
        """
        Evaluate all aspects of LLM response
        
        Args:
            query: User query
            response: LLM response
            context: Retrieved context
            
        Returns:
            Dictionary of evaluation scores
        """
        app_logger.info(f"Evaluating response for query: '{query[:50]}...'")
        
        metrics = {
            "relevance": self.evaluate_relevance(query, response, context),
            "coherence": self.evaluate_coherence(response),
            "factuality": self.evaluate_factuality(response, context),
            "completeness": self.evaluate_completeness(query, response),
        }
        
        # Calculate overall score
        metrics["overall"] = sum(metrics.values()) / len(metrics)
        
        app_logger.info("LLM Evaluation complete:")
        for metric, score in metrics.items():
            app_logger.info(f"  {metric}: {score:.3f}")
        
        return metrics


class SimpleEvaluator:
    """Simple heuristic-based evaluation (no LLM needed)"""

    @staticmethod
    def evaluate_length(response: str) -> float:
        """Evaluate if response has appropriate length"""
        word_count = len(response.split())
        
        if word_count < 20:
            return 0.3  # Too short
        elif word_count > 500:
            return 0.7  # Maybe too long
        else:
            return 1.0  # Good length

    @staticmethod
    def evaluate_citations(response: str) -> float:
        """Check if response includes citations"""
        # Look for citation patterns like [1], [Document 1], etc.
        citation_patterns = [
            r'\[\d+\]',
            r'\[Document \d+\]',
            r'\(.*\d{4}\)',  # (Author, 2024)
        ]
        
        has_citations = any(re.search(pattern, response) for pattern in citation_patterns)
        
        return 1.0 if has_citations else 0.5

    @staticmethod
    def evaluate_structure(response: str) -> float:
        """Evaluate response structure"""
        score = 0.0
        
        # Has paragraphs (multiple newlines)
        if '\n\n' in response or response.count('\n') > 2:
            score += 0.3
        
        # Has bullet points or numbered lists
        if re.search(r'^\s*[-•*\d]+[.)]', response, re.MULTILINE):
            score += 0.3
        
        # Has clear sections (headings indicated by colons or bold)
        if response.count(':') > 1 or response.count('**') > 2:
            score += 0.4
        
        return min(1.0, score)

    @staticmethod
    def evaluate_all(response: str) -> Dict[str, float]:
        """Run all simple evaluations"""
        metrics = {
            "length": SimpleEvaluator.evaluate_length(response),
            "citations": SimpleEvaluator.evaluate_citations(response),
            "structure": SimpleEvaluator.evaluate_structure(response),
        }
        
        metrics["overall"] = sum(metrics.values()) / len(metrics)
        
        return metrics


# Example usage
if __name__ == "__main__":
    # Sample data
    query = "What is the transformer architecture?"
    
    context = """
    [Document 1]
    The Transformer architecture uses self-attention mechanisms to process sequences.
    It was introduced in the paper "Attention Is All You Need" by Vaswani et al.
    """
    
    response = """The Transformer architecture is a neural network design that relies entirely on self-attention mechanisms instead of recurrence or convolution. 

Key components include:
1. Multi-head self-attention layers
2. Position-wise feed-forward networks
3. Positional encodings

As described in [Document 1], it was introduced by Vaswani et al. in "Attention Is All You Need" and has become the foundation for modern large language models."""
    
    # Simple evaluation (fast, no API calls)
    print("=== Simple Evaluation ===")
    simple_eval = SimpleEvaluator()
    simple_metrics = simple_eval.evaluate_all(response)
    for metric, score in simple_metrics.items():
        print(f"{metric}: {score:.3f}")
    
    # LLM evaluation (more accurate, requires API calls)
    print("\n=== LLM Evaluation (commented out to save API calls) ===")
    # evaluator = LLMEvaluator()
    # llm_metrics = evaluator.evaluate_all(query, response, context)
    # for metric, score in llm_metrics.items():
    #     print(f"{metric}: {score:.3f}")
