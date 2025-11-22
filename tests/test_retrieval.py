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


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])