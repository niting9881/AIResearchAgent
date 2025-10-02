"""Prompt templates for different use cases"""

from typing import Dict, List


class PromptTemplates:
    """Collection of prompt templates for RAG"""

    @staticmethod
    def get_system_prompt(style: str = "balanced") -> str:
        """
        Get system prompt based on style
        
        Args:
            style: Style of response ('concise', 'detailed', 'balanced', 'academic')
            
        Returns:
            System prompt string
        """
        prompts = {
            "concise": """You are an AI assistant helping researchers find information about Large Language Models. 
Provide concise, accurate answers based strictly on the provided context. 
Keep responses brief and to the point.""",
            
            "detailed": """You are an expert AI research assistant specializing in Large Language Models.
Provide comprehensive, detailed answers based on the provided context.
Include technical details, methodologies, and relevant citations.
Explain complex concepts clearly while maintaining academic rigor.""",
            
            "balanced": """You are a knowledgeable AI assistant helping researchers understand Large Language Models.
Provide clear, accurate answers based on the provided context.
Balance technical accuracy with accessibility.
Cite specific papers when relevant.""",
            
            "academic": """You are an academic research assistant with expertise in Large Language Models and Natural Language Processing.
Provide scholarly, well-referenced answers based on the provided research papers.
Use precise technical terminology and cite specific papers using [Document N] format.
Maintain an academic tone and highlight important research findings.""",
        }
        
        return prompts.get(style, prompts["balanced"])

    @staticmethod
    def build_rag_prompt(
        query: str,
        context: str,
        include_instructions: bool = True,
    ) -> str:
        """
        Build RAG prompt with query and context
        
        Args:
            query: User query
            context: Retrieved context
            include_instructions: Whether to include answer instructions
            
        Returns:
            Formatted prompt
        """
        instructions = ""
        if include_instructions:
            instructions = """
Instructions:
1. Answer based ONLY on the provided context
2. If the context doesn't contain enough information, say so
3. Cite specific documents using [Document N] format
4. Be clear and concise
5. If multiple papers discuss the topic, synthesize their perspectives

"""
        
        prompt = f"""{instructions}Context from research papers:
{context}

Question: {query}

Answer:"""
        
        return prompt

    @staticmethod
    def build_comparison_prompt(
        query: str,
        context: str,
    ) -> str:
        """Build prompt for comparison questions"""
        return f"""Context from research papers:
{context}

Question: {query}

Please provide a structured comparison addressing:
1. Key similarities between the approaches/models
2. Main differences and trade-offs
3. Specific strengths and weaknesses
4. Use cases where each excels
5. Citations to support your points

Answer:"""

    @staticmethod
    def build_summary_prompt(
        query: str,
        context: str,
    ) -> str:
        """Build prompt for summarization"""
        return f"""Context from research papers:
{context}

Question: {query}

Please provide a comprehensive summary that includes:
1. Main concepts and ideas
2. Key findings and contributions
3. Methodologies used
4. Impact and significance
5. Recent developments

Answer:"""

    @staticmethod
    def build_definition_prompt(
        query: str,
        context: str,
    ) -> str:
        """Build prompt for definitions"""
        return f"""Context from research papers:
{context}

Question: {query}

Please provide:
1. A clear, concise definition
2. Technical explanation (if applicable)
3. Examples of usage or applications
4. Related concepts
5. Citations from the papers

Answer:"""

    @staticmethod
    def build_tutorial_prompt(
        query: str,
        context: str,
    ) -> str:
        """Build prompt for tutorial-style answers"""
        return f"""Context from research papers:
{context}

Question: {query}

Please provide a tutorial-style answer that:
1. Explains the concept step-by-step
2. Uses clear, accessible language
3. Includes examples where relevant
4. Builds from basics to advanced concepts
5. Cites papers for deeper reading

Answer:"""

    @staticmethod
    def build_latest_prompt(
        query: str,
        context: str,
    ) -> str:
        """Build prompt for latest developments"""
        return f"""Context from recent research papers:
{context}

Question: {query}

Please provide an overview of the latest developments:
1. Most recent findings and advances
2. Emerging trends and directions
3. Notable papers and their contributions
4. Comparison with previous approaches
5. Future implications

Answer:"""

    @staticmethod
    def get_prompt_for_intent(
        query: str,
        context: str,
        intent: str = "research_question",
    ) -> str:
        """
        Get appropriate prompt based on query intent
        
        Args:
            query: User query
            context: Retrieved context
            intent: Query intent type
            
        Returns:
            Formatted prompt
        """
        intent_map = {
            "research_question": PromptTemplates.build_rag_prompt,
            "definition": PromptTemplates.build_definition_prompt,
            "comparison": PromptTemplates.build_comparison_prompt,
            "tutorial": PromptTemplates.build_tutorial_prompt,
            "latest_news": PromptTemplates.build_latest_prompt,
            "summary": PromptTemplates.build_summary_prompt,
        }
        
        prompt_builder = intent_map.get(intent, PromptTemplates.build_rag_prompt)
        return prompt_builder(query, context)


# Example usage
if __name__ == "__main__":
    # Sample context
    context = """
    [Document 1]
    Title: Attention Is All You Need
    Authors: Vaswani et al.
    Content: The Transformer architecture relies entirely on self-attention mechanisms...
    
    [Document 2]
    Title: BERT
    Authors: Devlin et al.
    Content: BERT uses bidirectional transformers for pre-training...
    """
    
    query = "What is the transformer architecture?"
    
    # Test different prompts
    print("=== Balanced Prompt ===")
    print(PromptTemplates.build_rag_prompt(query, context))
    
    print("\n=== Definition Prompt ===")
    print(PromptTemplates.build_definition_prompt(query, context))
    
    print("\n=== Comparison Prompt ===")
    comparison_query = "Compare transformer and BERT architectures"
    print(PromptTemplates.build_comparison_prompt(comparison_query, context))
