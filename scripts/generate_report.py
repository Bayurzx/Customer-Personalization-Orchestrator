#!/usr/bin/env python3
"""
Script: generate_report.py
Purpose: Convert experiment report notebook to PDF for stakeholder distribution.

Usage:
    python scripts/generate_report.py [--notebook path] [--output path]
"""

import argparse
import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def execute_notebook(notebook_path):
    """Execute notebook to generate outputs."""
    print(f"⚡ Executing notebook to generate outputs...")
    
    cmd = [
        "jupyter", "nbconvert",
        "--to", "notebook",
        "--execute",
        "--inplace",
        str(notebook_path)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✓ Notebook execution successful")
            return True
        else:
            print(f"❌ Notebook execution failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Notebook execution timed out (5 minutes)")
        return False
    except Exception as e:
        print(f"❌ Error during notebook execution: {e}")
        return False

def convert_to_html(notebook_path, html_path):
    """Convert notebook to HTML."""
    print(f"🌐 Converting {notebook_path} to HTML...")
    
    cmd = [
        "jupyter", "nbconvert",
        "--to", "html",
        "--output", str(html_path),
        str(notebook_path),
        "--no-input",  # Hide code cells
        "--embed-images"  # Embed images in HTML
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✓ HTML conversion successful")
            return True
        else:
            print(f"❌ HTML conversion failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ HTML conversion timed out")
        return False
    except Exception as e:
        print(f"❌ Error during HTML conversion: {e}")
        return False

def convert_html_to_pdf(html_path, pdf_path):
    """Convert HTML to PDF using weasyprint."""
    try:
        import weasyprint
        print("📄 Converting HTML to PDF using weasyprint...")
        
        # Add some basic CSS styling
        css_style = """
        @page {
            size: A4;
            margin: 2cm;
            @bottom-center {
                content: "Page " counter(page) " of " counter(pages);
                font-size: 10pt;
                color: #666;
            }
        }
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 11pt;
        }
        h1 {
            color: #0066cc;
            font-size: 24pt;
            margin-top: 0;
            page-break-after: avoid;
        }
        h2 {
            color: #0066cc;
            font-size: 18pt;
            margin-top: 1.5em;
            page-break-after: avoid;
        }
        h3 {
            color: #0066cc;
            font-size: 14pt;
            margin-top: 1em;
            page-break-after: avoid;
        }
        .jp-Cell {
            margin-bottom: 1em;
            page-break-inside: avoid;
        }
        .jp-OutputArea {
            margin-top: 0.5em;
        }
        img {
            max-width: 100%;
            height: auto;
            page-break-inside: avoid;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
            page-break-inside: avoid;
            font-size: 10pt;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
        }
        pre {
            background-color: #f8f8f8;
            padding: 10px;
            border-radius: 4px;
            font-size: 9pt;
            overflow-x: auto;
        }
        .highlight {
            background-color: #ffffcc;
            padding: 2px 4px;
        }
        """
        
        # Create CSS object
        css = weasyprint.CSS(string=css_style)
        
        # Convert HTML to PDF with better error handling
        html_doc = weasyprint.HTML(filename=str(html_path))
        html_doc.write_pdf(
            str(pdf_path), 
            stylesheets=[css],
            optimize_images=True
        )
        
        print("✓ PDF conversion successful")
        return True
        
    except ImportError:
        print("❌ weasyprint not available")
        return False
    except Exception as e:
        print(f"❌ PDF conversion failed: {e}")
        print(f"   Error details: {type(e).__name__}: {str(e)}")
        return False

def validate_pdf(pdf_path):
    """Validate the generated PDF."""
    if not os.path.exists(pdf_path):
        print("❌ PDF file not found")
        return False
    
    # Check file size
    file_size = os.path.getsize(pdf_path) / (1024 * 1024)  # MB
    print(f"📏 PDF file size: {file_size:.2f} MB")
    
    if file_size > 10:
        print("⚠️  PDF file size exceeds 10MB - consider optimizing")
    elif file_size < 0.1:
        print("⚠️  PDF file size is very small - may be incomplete")
    else:
        print("✓ PDF file size is reasonable")
    
    # Try to validate PDF structure (basic check)
    try:
        with open(pdf_path, 'rb') as f:
            header = f.read(8)
            if header.startswith(b'%PDF-'):
                print("✓ PDF file has valid header")
                return True
            else:
                print("❌ PDF file has invalid header")
                return False
    except Exception as e:
        print(f"❌ Error validating PDF: {e}")
        return False

def main():
    """Main function to generate PDF report."""
    parser = argparse.ArgumentParser(description="Generate PDF report from Jupyter notebook")
    parser.add_argument(
        "--notebook", 
        default="notebooks/05_experiment_report.ipynb",
        help="Path to the notebook file"
    )
    parser.add_argument(
        "--output", 
        default="reports/experiment_report.pdf",
        help="Output PDF path"
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip PDF validation"
    )
    parser.add_argument(
        "--keep-html",
        action="store_true",
        help="Keep intermediate HTML file for debugging"
    )
    
    args = parser.parse_args()
    
    # Convert to absolute paths
    notebook_path = Path(args.notebook).resolve()
    output_path = Path(args.output).resolve()
    html_path = output_path.with_suffix('.html')
    
    print("🚀 Starting PDF Report Generation")
    print(f"📓 Notebook: {notebook_path}")
    print(f"📄 Output: {output_path}")
    print()
    
    # Validate input
    if not notebook_path.exists():
        print(f"❌ Notebook not found: {notebook_path}")
        return 1
    
    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Execute notebook first to generate outputs
    if not execute_notebook(notebook_path):
        print("❌ Notebook execution failed")
        return 1
    
    print()
    
    # Convert notebook to HTML
    if not convert_to_html(notebook_path, html_path):
        print("❌ HTML generation failed")
        return 1
    
    print()
    
    # Convert HTML to PDF
    if not convert_html_to_pdf(html_path, output_path):
        print("❌ PDF generation failed")
        print(f"📄 HTML version available at: {html_path}")
        print("   You can manually convert HTML to PDF using your browser (Print -> Save as PDF)")
        return 1
    
    # Clean up HTML file (unless keeping it)
    if not args.keep_html:
        try:
            html_path.unlink()
            print("🧹 Cleaned up temporary HTML file")
        except:
            pass
    else:
        print(f"📄 HTML file kept at: {html_path}")
    
    print()
    
    # Validate PDF
    if not args.skip_validation:
        if not validate_pdf(output_path):
            print("❌ PDF validation failed")
            return 1
        print()
    
    print("🎉 PDF Report Generation Complete!")
    print(f"📄 Generated: {output_path}")
    print(f"🔗 File size: {os.path.getsize(output_path) / (1024 * 1024):.2f} MB")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())