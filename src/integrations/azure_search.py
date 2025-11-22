"""
Azure AI Search Integration Module

This module provides a wrapper around the Azure AI Search API for the Customer Personalization Orchestrator.
It handles index management, document indexing, and search operations.
"""

import os
from typing import List, Dict, Any, Optional
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_search_index_client() -> SearchIndexClient:
    """
    Create and return an Azure AI Search index client.
    
    Returns:
        SearchIndexClient: Configured client for index management
        
    Raises:
        ValueError: If required environment variables are missing
    """
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")
    
    if not endpoint or not admin_key:
        raise ValueError("Missing required Azure AI Search configuration")
    
    return SearchIndexClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(admin_key)
    )

def get_search_client(index_name: Optional[str] = None) -> SearchClient:
    """
    Create and return an Azure AI Search client for document operations.
    
    Args:
        index_name: Name of the index to search. If None, uses default from env.
        
    Returns:
        SearchClient: Configured client for search operations
        
    Raises:
        ValueError: If required environment variables are missing
    """
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    query_key = os.getenv("AZURE_SEARCH_QUERY_KEY")
    
    if not index_name:
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "approved-content-index")
    
    if not endpoint or not query_key:
        raise ValueError("Missing required Azure AI Search configuration")
    
    return SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(query_key)
    )

def index_exists(index_name: str) -> bool:
    """
    Check if an index exists.
    
    Args:
        index_name: Name of the index to check
        
    Returns:
        bool: True if index exists, False otherwise
    """
    try:
        client = get_search_index_client()
        client.get_index(index_name)
        return True
    except Exception:
        return False

def create_index(index_name: str) -> bool:
    """
    Create a search index (placeholder implementation).
    
    Args:
        index_name: Name of the index to create
        
    Returns:
        bool: True if successful
        
    Note:
        This is a placeholder. Full implementation will be in Task 2.1.
    """
    # This will be implemented in Task 2.1: Azure AI Search Index Setup
    print(f"Index creation for '{index_name}' will be implemented in Task 2.1")
    return True

if __name__ == "__main__":
    # Test the connection when run directly
    try:
        client = get_search_index_client()
        indexes = list(client.list_indexes())
        print(f"✅ Connected to Azure AI Search. Found {len(indexes)} indexes.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")