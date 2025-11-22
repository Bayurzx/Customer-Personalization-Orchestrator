"""
Unit tests for Azure AI Search integration.

Tests the search index creation, document indexing, and search operations
for the Customer Personalization Orchestrator.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from azure.search.documents.indexes.models import SearchIndex
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError

# Import the module under test
from src.integrations.azure_search import (
    get_search_index_client,
    get_search_client,
    create_content_index_schema,
    create_index,
    delete_index,
    index_exists,
    get_index_statistics,
    index_documents
)


class TestAzureSearchClients:
    """Test Azure Search client creation."""
    
    def test_get_search_index_client_success(self):
        """Test successful creation of search index client."""
        with patch.dict(os.environ, {
            'AZURE_SEARCH_ENDPOINT': 'https://test.search.windows.net',
            'AZURE_SEARCH_ADMIN_KEY': 'test-admin-key'
        }):
            client = get_search_index_client()
            assert client is not None
    
    def test_get_search_index_client_missing_config(self):
        """Test error handling when configuration is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Azure AI Search configuration"):
                get_search_index_client()
    
    def test_get_search_client_success(self):
        """Test successful creation of search client."""
        with patch.dict(os.environ, {
            'AZURE_SEARCH_ENDPOINT': 'https://test.search.windows.net',
            'AZURE_SEARCH_QUERY_KEY': 'test-query-key',
            'AZURE_SEARCH_INDEX_NAME': 'test-index'
        }):
            client = get_search_client()
            assert client is not None
    
    def test_get_search_client_with_custom_index(self):
        """Test search client creation with custom index name."""
        with patch.dict(os.environ, {
            'AZURE_SEARCH_ENDPOINT': 'https://test.search.windows.net',
            'AZURE_SEARCH_QUERY_KEY': 'test-query-key'
        }):
            client = get_search_client("custom-index")
            assert client is not None


class TestIndexSchema:
    """Test index schema creation."""
    
    def test_create_content_index_schema(self):
        """Test creation of content index schema."""
        index = create_content_index_schema("test-index")
        
        assert isinstance(index, SearchIndex)
        assert index.name == "test-index"
        
        # Check that all required fields are present
        field_names = [field.name for field in index.fields]
        expected_fields = [
            "document_id", "title", "content", "category", 
            "audience", "keywords", "approval_date", "source_url", 
            "metadata_author", "metadata_version", "metadata_last_updated"
        ]
        
        for field in expected_fields:
            assert field in field_names, f"Missing field: {field}"
        
        # Check that semantic search is configured
        assert index.semantic_search is not None
        assert len(index.semantic_search.configurations) == 1
        assert index.semantic_search.configurations[0].name == "default"
    
    def test_index_schema_field_properties(self):
        """Test that index fields have correct properties."""
        index = create_content_index_schema("test-index")
        
        # Find specific fields and check their properties
        field_dict = {field.name: field for field in index.fields}
        
        # document_id should be the key field
        doc_id_field = field_dict["document_id"]
        assert doc_id_field.key is True
        assert doc_id_field.filterable is True
        
        # title should be searchable
        title_field = field_dict["title"]
        assert title_field.searchable is True
        assert title_field.filterable is True
        
        # content should be searchable
        content_field = field_dict["content"]
        assert content_field.searchable is True


class TestIndexOperations:
    """Test index management operations."""
    
    @patch('src.integrations.azure_search.index_exists')
    @patch('src.integrations.azure_search.get_search_index_client')
    def test_create_index_success(self, mock_get_client, mock_exists):
        """Test successful index creation."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.create_index.return_value = Mock()
        mock_exists.return_value = False  # Index doesn't exist
        
        result = create_index("test-index")
        
        assert result is True
        mock_client.create_index.assert_called_once()
    
    @patch('src.integrations.azure_search.get_search_index_client')
    def test_create_index_already_exists(self, mock_get_client):
        """Test index creation when index already exists."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.create_index.side_effect = ResourceExistsError("Index exists")
        
        result = create_index("test-index")
        
        assert result is True  # Should still return True
    
    @patch('src.integrations.azure_search.index_exists')
    @patch('src.integrations.azure_search.get_search_index_client')
    def test_create_index_failure(self, mock_get_client, mock_exists):
        """Test index creation failure."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.create_index.side_effect = Exception("Creation failed")
        mock_exists.return_value = False  # Index doesn't exist
        
        result = create_index("test-index")
        
        assert result is False
    
    @patch('src.integrations.azure_search.get_search_index_client')
    def test_delete_index_success(self, mock_get_client):
        """Test successful index deletion."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        result = delete_index("test-index")
        
        assert result is True
        mock_client.delete_index.assert_called_once_with("test-index")
    
    @patch('src.integrations.azure_search.get_search_index_client')
    def test_delete_index_not_found(self, mock_get_client):
        """Test index deletion when index doesn't exist."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.delete_index.side_effect = ResourceNotFoundError("Index not found")
        
        result = delete_index("test-index")
        
        assert result is True  # Should still return True
    
    @patch('src.integrations.azure_search.get_search_index_client')
    def test_index_exists_true(self, mock_get_client):
        """Test index_exists when index exists."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.get_index.return_value = Mock()
        
        result = index_exists("test-index")
        
        assert result is True
    
    @patch('src.integrations.azure_search.get_search_index_client')
    def test_index_exists_false(self, mock_get_client):
        """Test index_exists when index doesn't exist."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.get_index.side_effect = Exception("Not found")
        
        result = index_exists("test-index")
        
        assert result is False


class TestDocumentIndexing:
    """Test document indexing operations."""
    
    @patch('src.integrations.azure_search.get_search_client_for_indexing')
    def test_index_documents_success(self, mock_get_client):
        """Test successful document indexing."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock successful upload results
        mock_result = [Mock(succeeded=True, key="doc1")]
        mock_client.upload_documents.return_value = mock_result
        
        documents = [
            {
                "document_id": "DOC001",
                "title": "Test Document",
                "content": "Test content",
                "category": "Test"
            }
        ]
        
        result = index_documents(documents, "test-index")
        
        assert result["indexed"] == 1
        assert result["failed"] == 0
        mock_client.upload_documents.assert_called_once()
    
    @patch('src.integrations.azure_search.get_search_client_for_indexing')
    def test_index_documents_partial_failure(self, mock_get_client):
        """Test document indexing with some failures."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock mixed results
        mock_result = [
            Mock(succeeded=True, key="doc1"),
            Mock(succeeded=False, key="doc2", error_message="Invalid document")
        ]
        mock_client.upload_documents.return_value = mock_result
        
        documents = [
            {"document_id": "DOC001", "title": "Test 1"},
            {"document_id": "DOC002", "title": "Test 2"}
        ]
        
        result = index_documents(documents, "test-index")
        
        assert result["indexed"] == 1
        assert result["failed"] == 1
    
    def test_index_documents_empty_list(self):
        """Test indexing with empty document list."""
        result = index_documents([], "test-index")
        
        assert result["indexed"] == 0
        assert result["failed"] == 0
    
    @patch('src.integrations.azure_search.get_search_client_for_indexing')
    def test_index_documents_batch_processing(self, mock_get_client):
        """Test document indexing with batch processing."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock different results for each batch call
        def mock_upload_side_effect(documents):
            # Return success for each document in the batch
            return [Mock(succeeded=True, key=doc["document_id"]) for doc in documents]
        
        mock_client.upload_documents.side_effect = mock_upload_side_effect
        
        # Create 7 documents to test batching (batch_size=3)
        documents = [
            {"document_id": f"DOC{i:03d}", "title": f"Test {i}"}
            for i in range(1, 8)
        ]
        
        result = index_documents(documents, "test-index", batch_size=3)
        
        # Should make 3 calls: 3 docs, 3 docs, 1 doc
        assert mock_client.upload_documents.call_count == 3
        assert result["indexed"] == 7  # 3 + 3 + 1
        assert result["failed"] == 0


class TestIndexStatistics:
    """Test index statistics operations."""
    
    @patch('src.integrations.azure_search.get_search_client_for_indexing')
    def test_get_index_statistics_success(self, mock_get_client):
        """Test successful retrieval of index statistics."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        mock_client.get_document_count.return_value = 42
        
        result = get_index_statistics("test-index")
        
        assert result is not None
        assert result["document_count"] == 42
    
    @patch('src.integrations.azure_search.get_search_client_for_indexing')
    def test_get_index_statistics_failure(self, mock_get_client):
        """Test index statistics retrieval failure."""
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.get_document_count.side_effect = Exception("Stats failed")
        
        result = get_index_statistics("test-index")
        
        assert result is None


class TestIntegrationOperations:
    """Test end-to-end integration operations."""
    
    @patch('src.integrations.azure_search.delete_index')
    @patch('src.integrations.azure_search.get_index_statistics')
    @patch('src.integrations.azure_search.index_documents')
    @patch('src.integrations.azure_search.index_exists')
    @patch('src.integrations.azure_search.create_index')
    def test_test_index_operations_success(self, mock_create, mock_exists, 
                                         mock_index_docs, mock_stats, mock_delete):
        """Test the complete test_index_operations function."""
        # Mock all operations to succeed
        mock_create.return_value = True
        mock_exists.return_value = True
        mock_index_docs.return_value = {"indexed": 1, "failed": 0}
        mock_stats.return_value = {"document_count": 1, "storage_size_bytes": 100}
        mock_delete.return_value = True
        
        # Import here to avoid pytest treating it as a test
        from src.integrations.azure_search import test_index_operations
        result = test_index_operations("test-index")
        
        assert result is True
        mock_create.assert_called_once_with("test-index")
        # index_exists is called multiple times (in test function and create_index)
        assert mock_exists.call_count >= 1
        mock_index_docs.assert_called_once()
        mock_stats.assert_called_once_with("test-index")
        # delete_index is called multiple times (cleanup + final cleanup)
        assert mock_delete.call_count >= 1
    
    @patch('src.integrations.azure_search.create_index')
    def test_test_index_operations_create_failure(self, mock_create):
        """Test test_index_operations when index creation fails."""
        mock_create.return_value = False
        
        # Import here to avoid pytest treating it as a test
        from src.integrations.azure_search import test_index_operations
        result = test_index_operations("test-index")
        
        assert result is False


# Sample data for testing
@pytest.fixture
def sample_content_document():
    """Provide a sample content document for testing."""
    return {
        "document_id": "DOC001",
        "title": "Premium Widget Features",
        "category": "Product",
        "content": "Our Premium Widget includes advanced features designed for valued customers.",
        "audience": "High-Value",
        "keywords": ["premium", "features", "upgrade", "exclusive"],
        "approval_date": "2025-11-01T00:00:00Z",
        "source_url": "https://example.com/content/premium-widget",
        "metadata": {
            "author": "Marketing Team",
            "version": "1.2",
            "last_updated": "2025-10-15"
        }
    }


class TestDocumentValidation:
    """Test document validation and schema compliance."""
    
    def test_sample_document_structure(self, sample_content_document):
        """Test that sample document has all required fields."""
        required_fields = [
            "document_id", "title", "category", "content", 
            "audience", "keywords", "approval_date", "source_url", "metadata"
        ]
        
        for field in required_fields:
            assert field in sample_content_document, f"Missing field: {field}"
        
        # Test metadata structure
        metadata = sample_content_document["metadata"]
        assert "author" in metadata
        assert "version" in metadata
        assert "last_updated" in metadata
    
    def test_keywords_as_list(self, sample_content_document):
        """Test that keywords field is a list."""
        keywords = sample_content_document["keywords"]
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        assert all(isinstance(kw, str) for kw in keywords)


class TestRetrievalAgent:
    """Test the retrieval agent functionality."""
    
    @patch('src.agents.retrieval_agent.get_search_client')
    def test_content_retriever_initialization(self, mock_get_client):
        """Test ContentRetriever initialization."""
        from src.agents.retrieval_agent import ContentRetriever
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        retriever = ContentRetriever()
        assert retriever.client == mock_client
    
    def test_content_retriever_with_custom_client(self):
        """Test ContentRetriever with custom client."""
        from src.agents.retrieval_agent import ContentRetriever
        
        mock_client = Mock()
        retriever = ContentRetriever(search_client=mock_client)
        assert retriever.client == mock_client
    
    def test_construct_query_from_segment_high_value(self):
        """Test query construction for high-value segment."""
        from src.agents.retrieval_agent import construct_query_from_segment
        
        segment = {
            "name": "High-Value Recent",
            "features": {
                "avg_order_value": 275.0,
                "avg_purchase_frequency": 14.5
            }
        }
        
        query = construct_query_from_segment(segment)
        
        # Should contain high-value related terms
        assert any(term in query.lower() for term in ['premium', 'exclusive', 'high-value', 'gold'])
        # Should contain loyalty terms due to high frequency
        assert 'loyalty' in query.lower()
    
    def test_construct_query_from_segment_at_risk(self):
        """Test query construction for at-risk segment."""
        from src.agents.retrieval_agent import construct_query_from_segment
        
        segment = {
            "name": "At-Risk",
            "features": {
                "engagement_score": 0.2
            }
        }
        
        query = construct_query_from_segment(segment)
        
        # Should contain retention-related terms
        assert any(term in query.lower() for term in ['retention', 'engagement', 'comeback'])
    
    def test_construct_query_from_segment_new_customer(self):
        """Test query construction for new customer segment."""
        from src.agents.retrieval_agent import construct_query_from_segment
        
        segment = {
            "name": "New Customer",
            "features": {}
        }
        
        query = construct_query_from_segment(segment)
        
        # Should contain new customer related terms
        assert any(term in query.lower() for term in ['welcome', 'getting started', 'introduction', 'new customer'])
    
    def test_construct_query_fallback(self):
        """Test query construction fallback for unknown segment."""
        from src.agents.retrieval_agent import construct_query_from_segment
        
        segment = {
            "name": "Unknown Segment",
            "features": {}
        }
        
        query = construct_query_from_segment(segment)
        
        # Should fallback to segment name or default
        assert query  # Should not be empty
    
    def test_extract_snippet_short_content(self):
        """Test snippet extraction with short content."""
        from src.agents.retrieval_agent import extract_snippet
        
        content = "This is a short piece of content."
        snippet = extract_snippet(content)
        
        assert snippet == content  # Should return full content
        assert not snippet.endswith("...")  # No truncation needed
    
    def test_extract_snippet_long_content(self):
        """Test snippet extraction with long content."""
        from src.agents.retrieval_agent import extract_snippet
        
        # Create content longer than SNIPPET_WORD_LIMIT (150 words)
        words = ["word"] * 200
        content = " ".join(words)
        
        snippet = extract_snippet(content)
        
        # Should be truncated
        assert snippet.endswith("...")
        assert len(snippet.split()) <= 150  # Should respect word limit
    
    def test_extract_snippet_empty_content(self):
        """Test snippet extraction with empty content."""
        from src.agents.retrieval_agent import extract_snippet
        
        snippet = extract_snippet("")
        assert snippet == ""
        
        snippet = extract_snippet(None)
        assert snippet == ""
    
    def test_extract_snippet_character_limit(self):
        """Test snippet extraction respects character limit."""
        from src.agents.retrieval_agent import extract_snippet
        
        # Create very long content
        content = "A" * 1000
        
        snippet = extract_snippet(content, max_length=100)
        
        assert len(snippet) <= 100
        assert snippet.endswith("...")
    
    @patch('src.agents.retrieval_agent.get_search_client')
    def test_retrieve_content_success(self, mock_get_client):
        """Test successful content retrieval."""
        from src.agents.retrieval_agent import ContentRetriever
        
        # Mock search client and results
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock search results
        mock_result = Mock()
        mock_result.get.side_effect = lambda key, default=None: {
            'document_id': 'DOC001',
            'title': 'Test Document',
            'content': 'This is test content for the document.',
            'category': 'Product',
            'audience': 'High-Value',
            '@search.score': 0.85
        }.get(key, default)
        
        mock_client.search.return_value = [mock_result]
        
        retriever = ContentRetriever()
        segment = {"name": "High-Value Recent", "features": {}}
        
        results = retriever.retrieve_content(segment, top_k=3)
        
        assert len(results) == 1
        assert results[0]['document_id'] == 'DOC001'
        assert results[0]['title'] == 'Test Document'
        assert results[0]['relevance_score'] == 0.85
        assert 'snippet' in results[0]
        assert 'retrieved_at' in results[0]
    
    @patch('src.agents.retrieval_agent.get_search_client')
    def test_retrieve_content_low_relevance_filtered(self, mock_get_client):
        """Test that low relevance results are filtered out."""
        from src.agents.retrieval_agent import ContentRetriever
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock result with low relevance score
        mock_result = Mock()
        mock_result.get.side_effect = lambda key, default=None: {
            'document_id': 'DOC001',
            'title': 'Test Document',
            'content': 'Test content',
            '@search.score': 0.3  # Below MIN_RELEVANCE_SCORE (0.5)
        }.get(key, default)
        
        mock_client.search.return_value = [mock_result]
        
        retriever = ContentRetriever()
        segment = {"name": "Test Segment", "features": {}}
        
        results = retriever.retrieve_content(segment)
        
        # Should be filtered out due to low relevance
        assert len(results) == 0
    
    @patch('src.agents.retrieval_agent.get_search_client')
    def test_retrieve_content_invalid_segment(self, mock_get_client):
        """Test error handling for invalid segment."""
        from src.agents.retrieval_agent import ContentRetriever
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        retriever = ContentRetriever()
        
        # Test with empty segment
        with pytest.raises(ValueError, match="Segment must contain 'name' field"):
            retriever.retrieve_content({})
        
        # Test with None segment
        with pytest.raises(ValueError, match="Segment must contain 'name' field"):
            retriever.retrieve_content(None)
    
    @patch('src.agents.retrieval_agent.get_search_client')
    def test_retrieve_content_search_error(self, mock_get_client):
        """Test error handling for search failures."""
        from src.agents.retrieval_agent import ContentRetriever
        from azure.core.exceptions import AzureError
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        mock_client.search.side_effect = AzureError("Search failed")
        
        retriever = ContentRetriever()
        segment = {"name": "Test Segment", "features": {}}
        
        with pytest.raises(AzureError):
            retriever.retrieve_content(segment)
    
    def test_convenience_functions(self):
        """Test convenience functions work correctly."""
        from src.agents.retrieval_agent import construct_query_from_segment, extract_snippet
        
        # Test construct_query_from_segment
        segment = {"name": "High-Value Recent", "features": {}}
        query = construct_query_from_segment(segment)
        assert isinstance(query, str)
        assert len(query) > 0
        
        # Test extract_snippet
        content = "This is test content for snippet extraction."
        snippet = extract_snippet(content)
        assert snippet == content


class TestRetrievalIntegration:
    """Test retrieval agent integration with search client."""
    
    @patch('src.agents.retrieval_agent.get_search_client')
    def test_retrieve_content_function(self, mock_get_client):
        """Test the convenience retrieve_content function."""
        from src.agents.retrieval_agent import retrieve_content
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock search results
        mock_result = Mock()
        mock_result.get.side_effect = lambda key, default=None: {
            'document_id': 'DOC001',
            'title': 'Test Document',
            'content': 'Test content',
            '@search.score': 0.75
        }.get(key, default)
        
        mock_client.search.return_value = [mock_result]
        
        segment = {"name": "High-Value Recent", "features": {}}
        results = retrieve_content(segment, top_k=5)
        
        assert len(results) == 1
        assert results[0]['document_id'] == 'DOC001'
        
        # Verify search was called with correct parameters
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        assert call_args[1]['top'] == 5
        assert call_args[1]['query_type'] == 'semantic'


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])