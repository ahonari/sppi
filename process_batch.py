"""
Batch processing script for multiple files
"""
import pandas as pd
from pathlib import Path
from datetime import datetime
from coder import ProtestCoder, DuplicateDetector
from config import Config

def process_batch():
    """Process ALL Excel files in the input folder"""
    
    print("="*60)
    print("📦 BATCH PROCESSING - ALL FILES")
    print("="*60)
    
    # Find all input files
    raw_dir = Config.RAW_DIR
    excel_files = list(raw_dir.glob('*.xlsx')) + list(raw_dir.glob('*.xls'))
    
    if not excel_files:
        print(f"❌ No Excel files found in {raw_dir}")
        print(f"   Please place your input files in: {raw_dir}")
        return None
    
    print(f"\n📁 Found {len(excel_files)} files to process:")
    for f in excel_files:
        print(f"   - {f.name}")
    
    total_articles = 0
    total_events = 0
    
    # Process each file
    for file_idx, input_file in enumerate(excel_files, 1):
        print(f"\n{'='*60}")
        print(f"📁 [{file_idx}/{len(excel_files)}] Processing: {input_file.name}")
        print(f"{'='*60}")
        
        try:
            # Load data
            df = pd.read_excel(input_file)
            print(f"   ✅ Loaded {len(df)} articles")
            
            # Filter for relevant articles
            if Config.RELEVANCE_COLUMN in df.columns:
                relevant_df = df[df[Config.RELEVANCE_COLUMN].str.lower().isin(['yes', '1', 'true', 'relevant'])]
                print(f"   📊 Found {len(relevant_df)} relevant articles out of {len(df)}")
                df = relevant_df
            else:
                print(f"   ⚠️ No '{Config.RELEVANCE_COLUMN}' column found. Processing all articles.")
            
            if df.empty:
                print("   ⚠️ No relevant articles to process")
                continue
            
            total_articles += len(df)
            
            # Initialize coder
            coder = ProtestCoder()
            
            # Process
            print("   🔄 Coding articles...")
            results_df = coder.process_batch(df)
            
            # Detect duplicates
            if not results_df.empty:
                print("   🔍 Detecting duplicates...")
                detector = DuplicateDetector()
                results_df = detector.detect_duplicates(results_df)
            
            # Remove large columns before saving
            for col in Config.EXCLUDE_COLUMNS:
                if col in results_df.columns:
                    results_df = results_df.drop(columns=[col])
            
            # Save results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = Config.PROCESSED_DIR / f'coded_{input_file.stem}_{timestamp}.xlsx'
            results_df.to_excel(output_file, index=False)
            print(f"   ✅ Results saved to: {output_file}")
            
            # Summary
            if not results_df.empty:
                total_events += len(results_df[results_df['relevance'] == 'Yes'])
                duplicates = len(results_df[results_df['duplicate'] == 'Yes'])
                print(f"\n   📊 Summary for {input_file.name}:")
                print(f"      Articles processed: {len(df)}")
                print(f"      Events coded: {len(results_df[results_df['relevance'] == 'Yes'])}")
                print(f"      Duplicates: {duplicates}")
                print(f"      Unique events: {len(results_df[results_df['duplicate'] != 'Yes'])}")
            
        except Exception as e:
            print(f"   ❌ Error processing {input_file.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Final summary
    print("\n" + "="*60)
    print("📊 BATCH PROCESSING COMPLETE")
    print("="*60)
    print(f"   Files processed: {len(excel_files)}")
    print(f"   Total articles: {total_articles}")
    print(f"   Total events coded: {total_events}")
    print(f"   Output folder: {Config.PROCESSED_DIR}")

if __name__ == "__main__":
    process_batch()