#!/usr/bin/env python3
"""
Content Indexing Pipeline Script

This script indexes all approved content documents from the data/content/approved_content/
directory into Azure AI Search. It processes documents in batches with progress tracking
and comprehensive error handling.

Usage:
    python scripts/index_content.py [--index-name INDEX_NAME] [--batch-size BATCH_SIZE] [--force]

Example:
    python scripts/index_content.py
    python scripts/index_content.py --index-name my-custom-index --batch-size 50
    python scripts/index_content.py --force  # Recreate index if exists
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from tqdm import tqdm

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.integrations.azure_search import (
    create_index,
    index_documents,
    index_exists,
    delete_index,
    get_index_statistics
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_content_documents(content_dir: str) -> List[Dict[str, Any]]:
    """
    Load all content documents from the specified directory.
    
    Args:
        content_dir: Path to the directory containing content JSON files
        
    Returns:
        List of document dictionaries
        
    Raises:
        FileNotFoundError: If content directory doesn't exist
        ValueError: If no valid documents found
    """
    content_path = Path(content_dir)
    
    if not content_path.exists():
        raise FileNotFoundError(f"Content directory not found: {content_dir}")
    
    documents = []
    json_files = list(content_path.glob("*.json"))
    
    if not json_files:
        raise ValueError(f"No JSON files found in {content_dir}")
    
    logger.info(f"📁 Found {len(json_files)} JSON files in {content_dir}")
    
    # Load documents with progress bar
    for file_path in tqdm(json_files, desc="Loading documents", unit="file"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                doc = json.load(f)
                
            # Validate required fields
            required_fields = ['document_id', 'title', 'content', 'category']
            missing_fields = [field for field in required_fields if field not in doc]
            
            if missing_fields:
                logger.warning(f"⚠️ Skipping {file_path.name}: missing fields {missing_fields}")
                continue
            
            # Add file metadata
            doc['_source_file'] = file_path.name
            doc['_loaded_at'] = datetime.utcnow().isoformat()
            
            documents.append(doc)
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in {file_path.name}: {e}")
            continue
        except Exception as e:
            logger.error(f"❌ Error loading {file_path.name}: {e}")
            continue
    
    if not documents:
        raise ValueError("No valid documents loaded")
    
    logger.info(f"✅ Successfully loaded {len(documents)} documents")
    return documents

def validate_documents(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and clean documents before indexing.
    
    Args:
        documents: List of document dictionaries
        
    Returns:
        List of validated documents
    """
    valid_documents = []
    
    for i, doc in enumerate(documents):
        try:
            # Check for duplicate document IDs
            doc_id = doc.get('document_id')
            if not doc_id:
                logger.warning(f"⚠️ Document {i+1}: missing document_id, skipping")
                continue
            
            # Check for existing document with same ID
            existing_ids = [d.get('document_id') for d in valid_documents]
            if doc_id in existing_ids:
                logger.warning(f"⚠️ Duplicate document_id '{doc_id}', skipping")
                continue
            
            # Validate content length
            content = doc.get('content', '')
            if len(content) < 50:
                logger.warning(f"⚠️ Document {doc_id}: content too short ({len(content)} chars), skipping")
                continue
            
            # Ensure required fields have values
            if not doc.get('title', '').strip():
                logger.warning(f"⚠️ Document {doc_id}: empty title, skipping")
                continue
            
            # Clean and normalize data
            doc['title'] = doc['title'].strip()
            doc['content'] = content.strip()
            doc['category'] = doc.get('category', 'General').strip()
            doc['audience'] = doc.get('audience', 'All').strip()
            
            # Ensure keywords is a list
            keywords = doc.get('keywords', [])
            if isinstance(keywords, str):
                doc['keywords'] = [kw.strip() for kw in keywords.split(',') if kw.strip()]
            elif not isinstance(keywords, list):
                doc['keywords'] = []
            
            # Ensure approval_date is properly formatted
            if 'approval_date' not in doc:
                doc['approval_date'] = datetime.utcnow().isoformat()
            
            # Ensure metadata exists
            if 'metadata' not in doc:
                doc['metadata'] = {}
            
            valid_documents.append(doc)
            
        except Exception as e:
            logger.error(f"❌ Error validating document {i+1}: {e}")
            continue
    
    logger.info(f"✅ Validated {len(valid_documents)} documents (filtered out {len(documents) - len(valid_documents)})")
    return valid_documents

def index_content_pipeline(
    content_dir: str = "data/content/approved_content",
    index_name: str = None,
    batch_size: int = 100,
    force_recreate: bool = False
) -> Dict[str, Any]:
    """
    Execute the complete content indexing pipeline.
    
    Args:
        content_dir: Directory containing content JSON files
        index_name: Name of the search index (uses default if None)
        batch_size: Number of documents to process per batch
        force_recreate: Whether to recreate the index if it exists
        
    Returns:
        Dictionary with indexing results and statistics
    """
    start_time = datetime.utcnow()
    
    try:
        # Use default index name if not provided
        if index_name is None:
            index_name = os.getenv("AZURE_SEARCH_INDEX_NAME", "approved-content-index")
        
        logger.info(f"🚀 Starting content indexing pipeline")
        logger.info(f"📂 Content directory: {content_dir}")
        logger.info(f"🔍 Target index: {index_name}")
        logger.info(f"📦 Batch size: {batch_size}")
        
        # Step 1: Check if index exists and handle force recreate
        if force_recreate and index_exists(index_name):
            logger.info(f"🗑️ Force recreate enabled, deleting existing index '{index_name}'")
            if not delete_index(index_name):
                raise Exception(f"Failed to delete existing index '{index_name}'")
        
        # Step 2: Create index if it doesn't exist
        if not index_exists(index_name):
            logger.info(f"🏗️ Creating search index '{index_name}'")
            if not create_index(index_name):
                raise Exception(f"Failed to create index '{index_name}'")
        else:
            logger.info(f"ℹ️ Using existing index '{index_name}'")
        
        # Step 3: Load content documents
        logger.info("📖 Loading content documents...")
        documents = load_content_documents(content_dir)
        
        # Step 4: Validate documents
        logger.info("🔍 Validating documents...")
        valid_documents = validate_documents(documents)
        
        if not valid_documents:
            raise ValueError("No valid documents to index")
        
        # Step 5: Index documents in batches
        logger.info(f"📤 Indexing {len(valid_documents)} documents in batches of {batch_size}...")
        
        indexing_result = index_documents(
            documents=valid_documents,
            index_name=index_name,
            batch_size=batch_size
        )
        
        # Step 6: Get final statistics
        final_stats = get_index_statistics(index_name)
        
        # Calculate execution time
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        # Compile results
        results = {
            "success": True,
            "index_name": index_name,
            "documents_loaded": len(documents),
            "documents_validated": len(valid_documents),
            "documents_indexed": indexing_result["indexed"],
            "documents_failed": indexing_result["failed"],
            "final_index_count": final_stats.get("document_count", 0) if final_stats else 0,
            "execution_time_seconds": round(execution_time, 2),
            "batch_size": batch_size,
            "started_at": start_time.isoformat(),
            "completed_at": end_time.isoformat()
        }
        
        # Log final summary
        logger.info("🎉 Content indexing pipeline completed successfully!")
        logger.info(f"📊 Summary:")
        logger.info(f"   • Documents loaded: {results['documents_loaded']}")
        logger.info(f"   • Documents validated: {results['documents_validated']}")
        logger.info(f"   • Documents indexed: {results['documents_indexed']}")
        logger.info(f"   • Documents failed: {results['documents_failed']}")
        logger.info(f"   • Final index count: {results['final_index_count']}")
        logger.info(f"   • Execution time: {results['execution_time_seconds']}s")
        
        return results
        
    except Exception as e:
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds()
        
        error_result = {
            "success": False,
            "error": str(e),
            "execution_time_seconds": round(execution_time, 2),
            "started_at": start_time.isoformat(),
            "failed_at": end_time.isoformat()
        }
        
        logger.error(f"❌ Content indexing pipeline failed: {e}")
        return error_result

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Index approved content documents into Azure AI Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/index_content.py
  python scripts/index_content.py --index-name my-custom-index
  python scripts/index_content.py --batch-size 50 --force
        """
    )
    
    parser.add_argument(
        "--content-dir",
        default="data/content/approved_content",
        help="Directory containing content JSON files (default: data/content/approved_content)"
    )
    
    parser.add_argument(
        "--index-name",
        help="Name of the search index (default: from AZURE_SEARCH_INDEX_NAME env var)"
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of documents to process per batch (default: 100)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Recreate the index if it already exists"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("🔧 Verbose logging enabled")
    
    try:
        # Execute the indexing pipeline
        results = index_content_pipeline(
            content_dir=args.content_dir,
            index_name=args.index_name,
            batch_size=args.batch_size,
            force_recreate=args.force
        )
        
        # Print final status
        if results["success"]:
            print(f"\n✅ SUCCESS: Indexed {results['documents_indexed']} documents successfully. {results['documents_failed']} errors.")
            sys.exit(0)
        else:
            print(f"\n❌ FAILED: {results['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Indexing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        sys.exit(1)

if __name__ == "__main__":
    main()