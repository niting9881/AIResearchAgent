"""Retrieval evaluation metrics"""

from typing import List, Dict, Tuple
import numpy as np

from src.utils.logger import app_logger


class RetrievalEvaluator:
    """Evaluate retrieval quality using various metrics"""

    @staticmethod
    def calculate_hit_rate(
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
    ) -> float:
        """
        Calculate hit rate (recall@k)
        
        Args:
            retrieved_docs: List of retrieved document IDs for each query
            relevant_docs: List of relevant document IDs for each query
            
        Returns:
            Hit rate (0-1)
        """
        hits = 0
        total = len(relevant_docs)
        
        for retrieved, relevant in zip(retrieved_docs, relevant_docs):
            retrieved_set = set(retrieved)
            relevant_set = set(relevant)
            
            if retrieved_set & relevant_set:  # Intersection
                hits += 1
        
        hit_rate = hits / total if total > 0 else 0
        
        app_logger.info(f"Hit Rate: {hit_rate:.3f} ({hits}/{total})")
        
        return hit_rate

    @staticmethod
    def calculate_mrr(
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
    ) -> float:
        """
        Calculate Mean Reciprocal Rank (MRR)
        
        Args:
            retrieved_docs: List of retrieved document IDs for each query
            relevant_docs: List of relevant document IDs for each query
            
        Returns:
            MRR score (0-1)
        """
        reciprocal_ranks = []
        
        for retrieved, relevant in zip(retrieved_docs, relevant_docs):
            relevant_set = set(relevant)
            
            # Find rank of first relevant document
            rank = 0
            for i, doc_id in enumerate(retrieved, 1):
                if doc_id in relevant_set:
                    rank = i
                    break
            
            if rank > 0:
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)
        
        mrr = np.mean(reciprocal_ranks) if reciprocal_ranks else 0
        
        app_logger.info(f"MRR: {mrr:.3f}")
        
        return float(mrr)

    @staticmethod
    def calculate_precision_at_k(
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
        k: int = 10,
    ) -> float:
        """
        Calculate Precision@K
        
        Args:
            retrieved_docs: Retrieved document IDs
            relevant_docs: Relevant document IDs
            k: Cutoff rank
            
        Returns:
            Precision@K score
        """
        precisions = []
        
        for retrieved, relevant in zip(retrieved_docs, relevant_docs):
            retrieved_k = retrieved[:k]
            relevant_set = set(relevant)
            
            relevant_retrieved = sum(1 for doc in retrieved_k if doc in relevant_set)
            precision = relevant_retrieved / k if k > 0 else 0
            precisions.append(precision)
        
        avg_precision = np.mean(precisions) if precisions else 0
        
        app_logger.info(f"Precision@{k}: {avg_precision:.3f}")
        
        return float(avg_precision)

    @staticmethod
    def calculate_recall_at_k(
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
        k: int = 10,
    ) -> float:
        """
        Calculate Recall@K
        
        Args:
            retrieved_docs: Retrieved document IDs
            relevant_docs: Relevant document IDs
            k: Cutoff rank
            
        Returns:
            Recall@K score
        """
        recalls = []
        
        for retrieved, relevant in zip(retrieved_docs, relevant_docs):
            retrieved_k = retrieved[:k]
            relevant_set = set(relevant)
            
            if len(relevant_set) == 0:
                continue
            
            relevant_retrieved = sum(1 for doc in retrieved_k if doc in relevant_set)
            recall = relevant_retrieved / len(relevant_set)
            recalls.append(recall)
        
        avg_recall = np.mean(recalls) if recalls else 0
        
        app_logger.info(f"Recall@{k}: {avg_recall:.3f}")
        
        return float(avg_recall)

    @staticmethod
    def calculate_ndcg(
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
        relevance_scores: List[List[float]] = None,
        k: int = 10,
    ) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain (NDCG@K)
        
        Args:
            retrieved_docs: Retrieved document IDs
            relevant_docs: Relevant document IDs
            relevance_scores: Optional relevance scores for each document
            k: Cutoff rank
            
        Returns:
            NDCG@K score
        """
        ndcg_scores = []
        
        for idx, (retrieved, relevant) in enumerate(zip(retrieved_docs, relevant_docs)):
            retrieved_k = retrieved[:k]
            relevant_set = set(relevant)
            
            # Calculate DCG
            dcg = 0
            for i, doc_id in enumerate(retrieved_k, 1):
                if doc_id in relevant_set:
                    # Use provided score or binary relevance
                    if relevance_scores and idx < len(relevance_scores):
                        rel = relevance_scores[idx].get(doc_id, 0)
                    else:
                        rel = 1
                    
                    dcg += rel / np.log2(i + 1)
            
            # Calculate IDCG (ideal DCG)
            if relevance_scores and idx < len(relevance_scores):
                ideal_scores = sorted([relevance_scores[idx].get(doc, 0) for doc in relevant], reverse=True)
            else:
                ideal_scores = [1] * len(relevant)
            
            idcg = sum(rel / np.log2(i + 2) for i, rel in enumerate(ideal_scores[:k]))
            
            # Calculate NDCG
            if idcg > 0:
                ndcg = dcg / idcg
            else:
                ndcg = 0
            
            ndcg_scores.append(ndcg)
        
        avg_ndcg = np.mean(ndcg_scores) if ndcg_scores else 0
        
        app_logger.info(f"NDCG@{k}: {avg_ndcg:.3f}")
        
        return float(avg_ndcg)

    @staticmethod
    def evaluate_all(
        retrieved_docs: List[List[str]],
        relevant_docs: List[List[str]],
        k: int = 10,
    ) -> Dict[str, float]:
        """
        Calculate all retrieval metrics
        
        Args:
            retrieved_docs: Retrieved document IDs
            relevant_docs: Relevant document IDs
            k: Cutoff rank
            
        Returns:
            Dictionary of all metrics
        """
        evaluator = RetrievalEvaluator()
        
        metrics = {
            "hit_rate": evaluator.calculate_hit_rate(retrieved_docs, relevant_docs),
            "mrr": evaluator.calculate_mrr(retrieved_docs, relevant_docs),
            f"precision@{k}": evaluator.calculate_precision_at_k(retrieved_docs, relevant_docs, k),
            f"recall@{k}": evaluator.calculate_recall_at_k(retrieved_docs, relevant_docs, k),
            f"ndcg@{k}": evaluator.calculate_ndcg(retrieved_docs, relevant_docs, k=k),
        }
        
        app_logger.info("Evaluation complete:")
        for metric, value in metrics.items():
            app_logger.info(f"  {metric}: {value:.3f}")
        
        return metrics


# Example usage
if __name__ == "__main__":
    # Sample data
    retrieved = [
        ["doc1", "doc2", "doc3", "doc4", "doc5"],
        ["doc2", "doc3", "doc1", "doc6", "doc7"],
        ["doc8", "doc9", "doc1", "doc2", "doc3"],
    ]
    
    relevant = [
        ["doc1", "doc3", "doc5"],
        ["doc1", "doc2"],
        ["doc1", "doc2", "doc4"],
    ]
    
    # Evaluate
    evaluator = RetrievalEvaluator()
    metrics = evaluator.evaluate_all(retrieved, relevant, k=5)
    
    print("\nResults:")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.3f}")
