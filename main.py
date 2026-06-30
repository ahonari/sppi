#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Protest Event Coding System
Main entry point for processing Iranian protest news articles
"""

import sys
import pandas as pd
from pathlib import Path
import argparse
from datetime import datetime

from config import Config
from coder import ProtestCoder, DuplicateDetector, ProtestCoderTest


def run_test_mode():
    """Run the system in test mode with sample data"""
    print("\n" + "="*60)
    print("🚀 RUNNING IN TEST MODE")
    print("="*60)
    
    results = ProtestCoderTest.run_test()
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Config.PROCESSED_DIR / f'test_results_{timestamp}.xlsx'
    results.to_excel(output_file, index=False)
    print(f"\n💾 Test results saved to: {output_file}")
    
    return results


def run_processing_mode(input_file: str = None):
    """Run the system in processing mode with actual data"""
    
    print("\n" + "="*60)
    print("🚀 RUNNING IN PROCESSING MODE")
    print("="*60)
    
    # Find input file
    if input_file is None:
        raw_dir = Config.RAW_DIR
        excel_files = list(raw_dir.glob('*.xlsx')) + list(raw_dir.glob('*.xls'))
        
        if not excel_files:
            print(f"❌ No Excel files found in {raw_dir}")
            print(f"   Please place your input file in: {raw_dir}")
            return None
        
        if len(excel_files) == 1:
            input_file = excel_files[0]
        else:
            print("\n📁 Multiple input files found:")
            for i, file in enumerate(excel_files):
                print(f"   {i+1}. {file.name}")
            choice = input("\nSelect file number (or press Enter for first): ").strip()
            if choice:
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(excel_files):
                        input_file = excel_files[idx]
                    else:
                        input_file = excel_files[0]
                except:
                    input_file = excel_files[0]
            else:
                input_file = excel_files[0]
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ Input file not found: {input_path}")
        return None
    
    print(f"\n📁 Input file: {input_path}")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = Config.PROCESSED_DIR / f'coded_protests_{timestamp}.xlsx'
    print(f"📁 Output file: {output_file}")
    
    # Load data
    try:
        print("\n📖 Loading data...")
        df = pd.read_excel(input_path)
        print(f"   ✅ Loaded {len(df)} articles")
        print(f"   Columns: {df.columns.tolist()}")
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return None
    
    # Initialize coder
    print("\n🔧 Initializing coder...")
    coder = ProtestCoder()
    
    # Process articles
    print("\n🔄 Processing articles...")
    results_df = coder.process_batch(df)
    
    # Detect duplicates
    if not results_df.empty:
        print("\n🔍 Detecting duplicates...")
        detector = DuplicateDetector()
        results_df = detector.detect_duplicates(results_df)
    
    # Save results
    try:
        print(f"\n💾 Saving results...")
        results_df.to_excel(output_file, index=False)
        print(f"   ✅ Excel file saved: {output_file}")
        
        csv_file = output_file.with_suffix('.csv')
        results_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        print(f"   ✅ CSV file saved: {csv_file}")
    except Exception as e:
        print(f"❌ Error saving results: {e}")
        return None
    
    # Summary
    print("\n" + "="*60)
    print("📊 PROCESSING SUMMARY")
    print("="*60)
    print(f"   Total articles: {len(df)}")
    if not results_df.empty:
        print(f"   Relevant events: {len(results_df[results_df['relevance'] == 'Yes'])}")
        print(f"   Duplicates: {len(results_df[results_df['duplicate'] == 'Yes'])}")
    print(f"   Output saved to: {output_file}")
    
    return results_df


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Protest Event Coding System')
    parser.add_argument('--test', action='store_true', help='Run in test mode with sample data')
    parser.add_argument('--input', type=str, help='Input Excel file path')
    parser.add_argument('--output', type=str, help='Output Excel file path')
    
    args = parser.parse_args()
    
    if args.test:
        run_test_mode()
    else:
        run_processing_mode(args.input)


if __name__ == "__main__":
    main()