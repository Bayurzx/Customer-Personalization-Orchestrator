"""
Azure AI Search Integration Module

This module provides a wrapper around the Azure AI Search API for the Customer Personalization Orchestrator.
It handles index management, document indexing, and search operations.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    ComplexField,
    SemanticConfiguration,
    SemanticPrioritizedFields,
    SemanticField,
    SemanticSearch
)
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

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

def create_content_index_schema(index_name: str) -> SearchIndex:
    """
    Create the search index schema for approved content documents.
    
    Args:
        index_name: Name of the index to create
        
    Returns:
        SearchIndex: Configured search index with proper schema
    """
    # Start with a minimal schema and build up
    fields = [
        # Primary key field
        SimpleField(
            name="document_id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
            sortable=True
        ),
        
        # Searchable text fields
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True,
            sortable=True
        ),
        
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
            searchable=True
        ),
        
        # Simple categorical fields
        SimpleField(
            name="category",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        
        SimpleField(
            name="audience",
            type=SearchFieldDataType.String,
            filterable=True,
            facetable=True
        ),
        
        # Keywords as a simple searchable string for now (we'll join the array)
        SearchableField(
            name="keywords",
            type=SearchFieldDataType.String,
            searchable=True,
            filterable=True
        ),
        
        # Date field
        SimpleField(
            name="approval_date",
            type=SearchFieldDataType.DateTimeOffset,
            filterable=True,
            sortable=True
        ),
        
        # URL field
        SimpleField(
            name="source_url",
            type=SearchFieldDataType.String,
            filterable=False
        ),
        
        # Metadata fields as separate simple fields (flatten the complex object)
        SimpleField(
            name="metadata_author",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        
        SimpleField(
            name="metadata_version",
            type=SearchFieldDataType.String,
            filterable=True
        ),
        
        SimpleField(
            name="metadata_last_updated",
            type=SearchFieldDataType.String,
            filterable=True
        )
    ]
    
    # Configure semantic search
    semantic_config = SemanticConfiguration(
        name="default",
        prioritized_fields=SemanticPrioritizedFields(
            title_field=SemanticField(field_name="title"),
            content_fields=[
                SemanticField(field_name="content")
            ],
            keywords_fields=[
                SemanticField(field_name="keywords")
            ]
        )
    )
    
    semantic_search = SemanticSearch(configurations=[semantic_config])
    
    # Create the index
    index = SearchIndex(
        name=index_name,
        fields=fields,
        semantic_search=semantic_search
    )
    
    return index

def create_index(index_name: str) -> bool:
    """
    Create a search index for approved content documents.
    
    Args:
        index_name: Name of the index to create
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        Exception: If index creation fails
    """
    try:
        # Check if index already exists first
        if index_exists(index_name):
            logger.info(f"ℹ️ Index '{index_name}' already exists")
            return True
            
        client = get_search_index_client()
        index = create_content_index_schema(index_name)
        
        # Try to create the index
        try:
            result = client.create_index(index)
            logger.info(f"✅ Successfully created index '{index_name}'")
            return True
        except ResourceExistsError:
            logger.info(f"ℹ️ Index '{index_name}' already exists (race condition)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create index '{index_name}': {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error setting up index client: {e}")
        return False

def delete_index(index_name: str) -> bool:
    """
    Delete a search index.
    
    Args:
        index_name: Name of the index to delete
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        client = get_search_index_client()
        client.delete_index(index_name)
        logger.info(f"✅ Successfully deleted index '{index_name}'")
        return True
    except ResourceNotFoundError:
        logger.warning(f"⚠️ Index '{index_name}' not found")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete index '{index_name}': {e}")
        return False

def get_index_statistics(index_name: str) -> Optional[Dict[str, Any]]:
    """
    Get statistics for a search index.
    
    Args:
        index_name: Name of the index
        
    Returns:
        Dict with index statistics or None if error
    """
    try:
        search_client = get_search_client_for_indexing(index_name)  # Use admin client for stats
        stats = search_client.get_document_count()
        
        return {
            "document_count": stats
        }
    except Exception as e:
        logger.error(f"❌ Failed to get statistics for index '{index_name}': {e}")
        return None

def get_search_client_for_indexing(index_name: Optional[str] = None) -> SearchClient:
    """
    Create and return an Azure AI Search client for indexing operations (requires admin key).
    
    Args:
        index_name: Name of the index to search. If None, uses default from env.
        
    Returns:
        SearchClient: Configured client for indexing operations
        
    Raises:
        ValueError: If required environment variables are missing
    """
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    admin_key = os.getenv("AZURE_SEARCH_ADMIN_KEY")  # Use admin key for indexing
    
    if not index_name:
        index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "approved-content-index")
    
    if not endpoint or not admin_key:
        raise ValueError("Missing required Azure AI Search configuration for indexing")
    
    return SearchClient(
        endpoint=endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(admin_key)
    )

def transform_document_for_indexing(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a document to match the search index schema.
    
    Args:
        doc: Original document dictionary
        
    Returns:
        Transformed document ready for indexing
    """
    transformed = {
        "document_id": doc.get("document_id"),
        "title": doc.get("title"),
        "content": doc.get("content"),
        "category": doc.get("category"),
        "audience": doc.get("audience"),
        "approval_date": doc.get("approval_date"),
        "source_url": doc.get("source_url", "")
    }
    
    # Transform keywords array to a space-separated string
    keywords = doc.get("keywords", [])
    if isinstance(keywords, list):
        transformed["keywords"] = " ".join(keywords)
    else:
        transformed["keywords"] = str(keywords) if keywords else ""
    
    # Flatten metadata object
    metadata = doc.get("metadata", {})
    transformed["metadata_author"] = metadata.get("author", "")
    transformed["metadata_version"] = metadata.get("version", "")
    transformed["metadata_last_updated"] = metadata.get("last_updated", "")
    
    return transformed

def index_documents(documents: List[Dict[str, Any]], index_name: Optional[str] = None, batch_size: int = 100) -> Dict[str, int]:
    """
    Index a list of documents into Azure AI Search.
    
    Args:
        documents: List of document dictionaries to index
        index_name: Name of the index (uses default if None)
        batch_size: Number of documents to process in each batch
        
    Returns:
        Dict with indexing statistics (indexed, failed)
    """
    if not documents:
        logger.warning("No documents provided for indexing")
        return {"indexed": 0, "failed": 0}
    
    try:
        search_client = get_search_client_for_indexing(index_name)
        total_indexed = 0
        total_failed = 0
        
        # Transform documents to match schema
        transformed_docs = [transform_document_for_indexing(doc) for doc in documents]
        
        # Process documents in batches
        for i in range(0, len(transformed_docs), batch_size):
            batch = transformed_docs[i:i + batch_size]
            
            try:
                # Upload the batch
                result = search_client.upload_documents(documents=batch)
                
                # Count successes and failures
                succeeded = len([r for r in result if r.succeeded])
                failed = len([r for r in result if not r.succeeded])
                
                total_indexed += succeeded
                total_failed += failed
                
                logger.info(f"Batch {i//batch_size + 1}: {succeeded} indexed, {failed} failed")
                
                # Log any failures
                for r in result:
                    if not r.succeeded:
                        logger.error(f"Failed to index document {r.key}: {r.error_message}")
                        
            except Exception as e:
                logger.error(f"Batch indexing error: {e}")
                total_failed += len(batch)
        
        logger.info(f"✅ Indexing complete: {total_indexed} indexed, {total_failed} failed")
        return {"indexed": total_indexed, "failed": total_failed}
        
    except Exception as e:
        logger.error(f"❌ Error during document indexing: {e}")
        return {"indexed": 0, "failed": len(documents)}

def test_index_operations(index_name: str = None) -> bool:
    """
    Test index creation, document indexing, and cleanup.
    
    Args:
        index_name: Name of the test index
        
    Returns:
        bool: True if all tests pass
    """
    try:
        # Generate unique index name if not provided
        if index_name is None:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            index_name = f"test-index-{timestamp}"
        
        logger.info(f"🧪 Testing index operations with '{index_name}'")
        
        # Clean up any existing test index first
        if index_exists(index_name):
            logger.info(f"🧹 Cleaning up existing test index '{index_name}'")
            delete_index(index_name)
        
        # Test 1: Create index
        if not create_index(index_name):
            logger.error("❌ Index creation test failed")
            return False
        
        # Test 2: Check if index exists
        if not index_exists(index_name):
            logger.error("❌ Index existence check failed")
            return False
        
        # Test 3: Index a test document (simplified for testing)
        test_doc = {
            "@search.action": "upload",  # Explicitly specify the action
            "document_id": "TEST001",
            "title": "Test Document",
            "category": "Test",
            "content": "This is a test document for validating the search index.",
            "audience": "All",
            "keywords": ["test", "validation"],
            "approval_date": datetime.utcnow().isoformat(),
            "source_url": "https://example.com/test"
            # Skip metadata for now to isolate the issue
        }
        
        result = index_documents([test_doc], index_name)
        if result["indexed"] != 1:
            logger.error("❌ Document indexing test failed")
            return False
        
        # Test 4: Get index statistics
        stats = get_index_statistics(index_name)
        if stats is None:
            logger.error("❌ Index statistics test failed")
            return False
        
        logger.info(f"📊 Index statistics: {stats}")
        
        # Test 5: Clean up - delete test index
        if not delete_index(index_name):
            logger.error("❌ Index deletion test failed")
            return False
        
        logger.info("✅ All index operation tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    # Configure logging for direct execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test the connection when run directly
    try:
        client = get_search_index_client()
        indexes = list(client.list_indexes())
        print(f"✅ Connected to Azure AI Search. Found {len(indexes)} indexes.")
        
        # Run comprehensive tests
        if test_index_operations():
            print("🎉 All tests passed! Azure AI Search integration is working correctly.")
        else:
            print("❌ Some tests failed. Check the logs for details.")
            
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("💡 Make sure your Azure AI Search credentials are configured in .env")
