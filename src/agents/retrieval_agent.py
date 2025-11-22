"""
Module: retrieval_agent.py
Purpose: Content retrieval logic for segment-based queries.

This module implements the Retrieval Agent responsible for retrieving
relevant approved content from the indexed corpus to ground message generation.
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from azure.search.documents import SearchClient
from azure.core.exceptions import AzureError

from src.integrations.azure_search import get_search_client

# Configure logger
logger = logging.getLogger(__name__)

# Retrieval constants
DEFAULT_TOP_K = 5
MIN_RELEVANCE_SCORE = 0.5
MAX_SNIPPET_LENGTH = 200
SNIPPET_WORD_LIMIT = 150  # Approximately 150-200 words


class ContentRetriever:
    """
    Content retrieval agent for segment-based queries.
    
    This class handles the retrieval of relevant approved content
    from Azure AI Search based on customer segment characteristics.
    """
    
    def __init__(self, search_client: Optional[SearchClient] = None):
        """
        Initialize the content retriever.
        
        Args:
            search_client: Optional Azure Search client. If None, creates default client.
        """
        self.client = search_client or get_search_client()
        logger.info("ContentRetriever initialized")
    
    def retrieve_content(
        self, 
        segment: Dict[str, Any], 
        top_k: int = DEFAULT_TOP_K
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant content for a customer segment.
        
        Args:
            segment: Segment information with name and features
            top_k: Number of results to return (default: 5)
            
        Returns:
            List of retrieved content with snippets and metadata
            
        Raises:
            ValueError: If segment is invalid
            AzureError: If search operation fails
        """
        if not segment or 'name' not in segment:
            raise ValueError("Segment must contain 'name' field")
        
        logger.info(f"Retrieving content for segment: {segment['name']}")
        
        try:
            # Construct search query from segment characteristics
            query = self.construct_query_from_segment(segment)
            logger.debug(f"Constructed query: '{query}'")
            
            # Perform search with semantic ranking
            search_results = self.client.search(
                search_text=query,
                top=top_k,
                query_type="semantic",
                semantic_configuration_name="default",
                select=["document_id", "title", "content", "category", "audience"],
                include_total_count=True
            )
            
            # Process and format results
            retrieved_content = []
            for result in search_results:
                # Extract relevance score
                relevance_score = result.get('@search.score', 0.0)
                
                # Apply relevance threshold
                if relevance_score < MIN_RELEVANCE_SCORE:
                    logger.debug(f"Skipping document {result.get('document_id')} with low relevance: {relevance_score}")
                    continue
                
                # Extract snippet from content
                snippet = self.extract_snippet(result.get('content', ''))
                
                content_item = {
                    "document_id": result.get('document_id'),
                    "title": result.get('title'),
                    "snippet": snippet,
                    "relevance_score": relevance_score,
                    "paragraph_index": 0,  # Simplified for POC
                    "category": result.get('category'),
                    "audience": result.get('audience'),
                    "retrieved_at": datetime.utcnow().isoformat()
                }
                
                retrieved_content.append(content_item)
            
            logger.info(f"Retrieved {len(retrieved_content)} relevant documents for segment '{segment['name']}'")
            
            # Log query and results for audit
            self._log_retrieval_operation(segment, query, retrieved_content)
            
            return retrieved_content
            
        except AzureError as e:
            logger.error(f"Azure Search error during retrieval: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during content retrieval: {e}")
            raise
    
    def construct_query_from_segment(self, segment: Dict[str, Any]) -> str:
        """
        Construct search query from segment characteristics.
        
        Args:
            segment: Segment information with name and features
            
        Returns:
            Search query string optimized for the segment
        """
        query_terms = []
        
        # Base query from segment name
        segment_name = segment.get('name', '').lower()
        
        # Map segment names to search terms
        if 'high-value' in segment_name or 'premium' in segment_name:
            query_terms.extend(['premium', 'exclusive', 'high-value', 'gold'])
        elif 'at-risk' in segment_name:
            query_terms.extend(['retention', 'engagement', 'comeback', 'special offer'])
        elif 'new' in segment_name:
            query_terms.extend(['welcome', 'getting started', 'introduction', 'new customer'])
        elif 'loyal' in segment_name or 'frequent' in segment_name:
            query_terms.extend(['loyalty', 'rewards', 'frequent', 'thank you'])
        else:
            # Standard segment - use general terms
            query_terms.extend(['features', 'benefits', 'products'])
        
        # Add feature-based terms if available
        features = segment.get('features', {})
        
        # High order value suggests premium content
        if features.get('avg_order_value', 0) > 200:
            query_terms.append('premium')
        
        # High purchase frequency suggests loyalty content
        if features.get('avg_purchase_frequency', 0) > 10:
            query_terms.append('loyalty')
        
        # Low engagement suggests retention content
        if features.get('engagement_score', 1.0) < 0.3:
            query_terms.append('retention')
        
        # Construct final query
        query = ' '.join(set(query_terms))  # Remove duplicates
        
        # Fallback to segment name if no terms generated
        if not query.strip():
            query = segment.get('name', 'products')
        
        return query
    
    def extract_snippet(self, content: str, max_length: int = MAX_SNIPPET_LENGTH) -> str:
        """
        Extract a snippet from document content.
        
        Args:
            content: Full document content
            max_length: Maximum snippet length in characters
            
        Returns:
            Extracted snippet (approximately 150-200 words)
        """
        if not content:
            return ""
        
        # Clean the content
        content = content.strip()
        
        # Split into words to respect word boundaries
        words = content.split()
        
        # Limit to approximately SNIPPET_WORD_LIMIT words
        if len(words) <= SNIPPET_WORD_LIMIT:
            snippet = content
        else:
            # Take first SNIPPET_WORD_LIMIT words
            snippet_words = words[:SNIPPET_WORD_LIMIT]
            snippet = ' '.join(snippet_words)
            
            # Add ellipsis if truncated
            if len(words) > SNIPPET_WORD_LIMIT:
                snippet += "..."
        
        # Ensure we don't exceed character limit
        if len(snippet) > max_length:
            snippet = snippet[:max_length - 3] + "..."
        
        return snippet
    
    def _log_retrieval_operation(
        self, 
        segment: Dict[str, Any], 
        query: str, 
        results: List[Dict[str, Any]]
    ) -> None:
        """
        Log retrieval operation for audit purposes.
        
        Args:
            segment: Segment information
            query: Search query used
            results: Retrieved results
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation": "content_retrieval",
            "segment_name": segment.get('name'),
            "query": query,
            "results_count": len(results),
            "document_ids": [r.get('document_id') for r in results],
            "avg_relevance_score": sum(r.get('relevance_score', 0) for r in results) / max(1, len(results))
        }
        
        logger.info(f"Retrieval operation: {log_entry}")


# Convenience functions for direct usage
def retrieve_content(segment: Dict[str, Any], top_k: int = DEFAULT_TOP_K) -> List[Dict[str, Any]]:
    """
    Convenience function to retrieve content for a segment.
    
    Args:
        segment: Segment information with name and features
        top_k: Number of results to return
        
    Returns:
        List of retrieved content with snippets
    """
    retriever = ContentRetriever()
    return retriever.retrieve_content(segment, top_k)


def construct_query_from_segment(segment: Dict[str, Any]) -> str:
    """
    Convenience function to construct query from segment.
    
    Args:
        segment: Segment information
        
    Returns:
        Search query string
    """
    retriever = ContentRetriever()
    return retriever.construct_query_from_segment(segment)


def extract_snippet(content: str, max_length: int = MAX_SNIPPET_LENGTH) -> str:
    """
    Convenience function to extract snippet from content.
    
    Args:
        content: Full document content
        max_length: Maximum snippet length
        
    Returns:
        Extracted snippet
    """
    retriever = ContentRetriever()
    return retriever.extract_snippet(content, max_length)


if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the retrieval agent
    try:
        # Test segment
        test_segment = {
            "name": "High-Value Recent",
            "features": {
                "avg_order_value": 275.0,
                "avg_purchase_frequency": 14.5,
                "engagement_score": 0.48
            }
        }
        
        print(f"🧪 Testing retrieval for segment: {test_segment['name']}")
        
        # Test query construction
        query = construct_query_from_segment(test_segment)
        print(f"📝 Constructed query: '{query}'")
        
        # Test content retrieval
        results = retrieve_content(test_segment, top_k=3)
        print(f"📊 Retrieved {len(results)} documents")
        
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['title']} (score: {result['relevance_score']:.2f})")
            print(f"     Snippet: {result['snippet'][:100]}...")
        
        print("✅ Retrieval agent test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test execution failed: {e}")