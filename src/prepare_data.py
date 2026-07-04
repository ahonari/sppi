"""
Data Preparation Script for Protest Dashboard

This script:
1. Merges all Excel and CSV files from data/processed/
2. Removes duplicates (duplicate = "Yes")
3. Geocodes combined location (arena_name + event_location_name) to get lat/lng
4. Uses free Nominatim (OpenStreetMap) geocoding
5. Saves the final merged file for visualization
"""

import pandas as pd
import os
import time
import json
import re
from pathlib import Path
from typing import Dict, Optional, Tuple
import requests
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# ============================================================
# CONFIGURATION
# ============================================================

# Paths
BASE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
OUTPUT_DIR = BASE_DIR / 'data' / 'dashboard'
GEOCODE_CACHE_FILE = BASE_DIR / 'data' / 'geocode_cache.json'

# Create output directory
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# GEOCODE CACHE MANAGEMENT
# ============================================================

class GeocodeCache:
    """Simple cache for geocoding results to avoid repeated API calls"""
    
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from file"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to file"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def get(self, location: str) -> Optional[Dict]:
        """Get cached geocode result"""
        if location in self.cache:
            return self.cache[location]
        return None
    
    def set(self, location: str, result: Dict):
        """Cache geocode result"""
        self.cache[location] = result
        self._save_cache()
    
    def __contains__(self, location: str) -> bool:
        return location in self.cache


class Geocoder:
    """Geocode locations using free Nominatim (OpenStreetMap) API"""
    
    def __init__(self):
        self.cache = GeocodeCache(GEOCODE_CACHE_FILE)
        # Set a user agent (required by Nominatim)
        self.user_agent = "ProtestDashboard/1.0 (research project)"
        self.base_url = "https://nominatim.openstreetmap.org/search"
        
        # Common cities and their approximate coordinates
        self.city_coords = {
            'تهران': {'lat': 35.6892, 'lng': 51.3890},
            'اصفهان': {'lat': 32.6539, 'lng': 51.6660},
            'مشهد': {'lat': 36.2605, 'lng': 59.6168},
            'شیراز': {'lat': 29.5918, 'lng': 52.5837},
            'تبریز': {'lat': 38.0800, 'lng': 46.2919},
            'اهواز': {'lat': 31.3183, 'lng': 48.6706},
            'کرج': {'lat': 35.8355, 'lng': 50.9391},
            'قم': {'lat': 34.6399, 'lng': 50.8759},
            'رشت': {'lat': 37.2761, 'lng': 49.5886},
            'کرمانشاه': {'lat': 34.3277, 'lng': 47.0778},
            'ارومیه': {'lat': 37.5553, 'lng': 45.0725},
            'زاهدان': {'lat': 29.4963, 'lng': 60.8629},
            'همدان': {'lat': 34.7983, 'lng': 48.5146},
            'کرمان': {'lat': 30.2839, 'lng': 57.0834},
            'یزد': {'lat': 31.8974, 'lng': 54.3569},
            'اردبیل': {'lat': 38.2498, 'lng': 48.2933},
            'بندرعباس': {'lat': 27.1832, 'lng': 56.2665},
            'اراک': {'lat': 34.0868, 'lng': 49.6894},
            'قزوین': {'lat': 36.2704, 'lng': 50.0037},
            'زنجان': {'lat': 36.6736, 'lng': 48.4787},
            'سنندج': {'lat': 35.3090, 'lng': 46.9905},
            'ساری': {'lat': 36.5633, 'lng': 53.0601},
            'گرگان': {'lat': 36.8457, 'lng': 54.4394},
            'خرم‌آباد': {'lat': 33.4878, 'lng': 48.3558},
            'بوشهر': {'lat': 28.9234, 'lng': 50.8203},
            'ایلام': {'lat': 33.6360, 'lng': 46.4227},
            'بجنورد': {'lat': 37.4752, 'lng': 57.3337},
            'شهرکرد': {'lat': 32.3255, 'lng': 50.8452},
            'بیرجند': {'lat': 32.8662, 'lng': 59.2211},
            'یاسوج': {'lat': 30.6681, 'lng': 51.5875},
            'سمنان': {'lat': 35.5769, 'lng': 53.3921},
            'چابهار': {'lat': 25.2919, 'lng': 60.6430},
            'سراوان': {'lat': 27.3707, 'lng': 62.3345},
            'زابل': {'lat': 31.0283, 'lng': 61.4982},
            'ایرانشهر': {'lat': 27.2024, 'lng': 60.6847},
            'مهدیشهر': {'lat': 35.7100, 'lng': 53.3530},
            'شهمیرزاد': {'lat': 35.7500, 'lng': 53.3500},
            'پرند': {'lat': 35.4900, 'lng': 50.9500},
            'تهرانسر': {'lat': 35.6900, 'lng': 51.2900},
            'سامان': {'lat': 32.4520, 'lng': 50.9100},
            'گیلانغرب': {'lat': 34.1400, 'lng': 45.9100},
            'بانه': {'lat': 35.9980, 'lng': 45.8820},
            'کوهک': {'lat': 27.3700, 'lng': 62.3300},
            'نکا': {'lat': 36.6500, 'lng': 53.3000},
            'آبادان': {'lat': 30.3390, 'lng': 48.3040},
            'خرمشهر': {'lat': 30.4400, 'lng': 48.1800},
            'دزفول': {'lat': 32.3830, 'lng': 48.4000},
            'گچساران': {'lat': 30.3500, 'lng': 50.8000},
            'قائنات': {'lat': 33.7200, 'lng': 59.1800},
            'کاشان': {'lat': 33.9850, 'lng': 51.4400},
            'ساوه': {'lat': 35.0200, 'lng': 50.3400},
            'شاهرود': {'lat': 36.4200, 'lng': 54.9700},
            'بروجرد': {'lat': 33.8940, 'lng': 48.7600},
            'کوهدشت': {'lat': 33.5350, 'lng': 47.6100},
            'ایذه': {'lat': 31.8350, 'lng': 49.8700},
            'نیشابور': {'lat': 36.2100, 'lng': 58.8200},
            'هرسین': {'lat': 34.2700, 'lng': 47.5900},
            'اسدآباد': {'lat': 34.7800, 'lng': 48.1200},
            'نهاوند': {'lat': 34.1900, 'lng': 48.3700},
            'خلیل‌آباد': {'lat': 35.2500, 'lng': 58.2900},
            'چالدران': {'lat': 39.0600, 'lng': 44.3800},
            'ماکو': {'lat': 39.2900, 'lng': 44.5200},
            'سلماس': {'lat': 38.2100, 'lng': 44.7600},
            'پیرانشهر': {'lat': 36.7000, 'lng': 45.1500},
            'بابلسر': {'lat': 36.7000, 'lng': 52.6500},
            'تنکابن': {'lat': 36.8000, 'lng': 50.8800},
            'رامسر': {'lat': 36.9000, 'lng': 50.6500},
            'چالوس': {'lat': 36.6500, 'lng': 51.4200},
            'نوشهر': {'lat': 36.6500, 'lng': 51.5000},
            'بهشهر': {'lat': 36.7000, 'lng': 53.5500},
            'قائم‌شهر': {'lat': 36.4600, 'lng': 52.8600},
            'آمل': {'lat': 36.4700, 'lng': 52.3500},
            'بابل': {'lat': 36.5500, 'lng': 52.6800},
            'نائین': {'lat': 32.8600, 'lng': 53.0800},
            'اردکان': {'lat': 32.3100, 'lng': 54.0200},
            'میبد': {'lat': 32.2400, 'lng': 54.0200},
            'تفت': {'lat': 31.7400, 'lng': 54.2000},
            'بافق': {'lat': 31.6000, 'lng': 55.4000},
            'رفسنجان': {'lat': 30.4000, 'lng': 56.0000},
            'سیرجان': {'lat': 29.4500, 'lng': 55.6800},
            'جیرفت': {'lat': 28.6800, 'lng': 57.7400},
            'بم': {'lat': 29.1000, 'lng': 58.3500},
            'زرقان': {'lat': 29.7800, 'lng': 52.7200},
            'مرودشت': {'lat': 29.8700, 'lng': 52.8000},
            'کازرون': {'lat': 29.6200, 'lng': 51.6500},
            'فسا': {'lat': 28.9400, 'lng': 53.6500},
            'داراب': {'lat': 28.7500, 'lng': 54.5500},
            'اقلید': {'lat': 30.9000, 'lng': 52.7000},
            'لارستان': {'lat': 27.6800, 'lng': 54.3400},
            'جهرم': {'lat': 28.5000, 'lng': 53.5600},
            'فیروزآباد': {'lat': 28.8400, 'lng': 52.5700},
        }
    
    def geocode(self, arena_name: str, event_location_name: str = None) -> Tuple[Optional[float], Optional[float]]:
        """
        Geocode a location using Nominatim (OpenStreetMap).
        
        Args:
            arena_name: Specific location (e.g., "مقابل مجلس شورای اسلامی")
            event_location_name: City/town/village (e.g., "تهران")
        
        Returns:
            (lat, lng) tuple or (None, None) if geocoding fails
        """
        # Handle NaN or None values - convert to string and clean
        if arena_name is None or (isinstance(arena_name, float) and pd.isna(arena_name)):
            arena_name = ''
        else:
            arena_name = str(arena_name).strip()
        
        if event_location_name is None or (isinstance(event_location_name, float) and pd.isna(event_location_name)):
            event_location_name = ''
        else:
            event_location_name = str(event_location_name).strip()
        
        # If both are empty/unknown, return None
        if (not arena_name or arena_name in ['Unknown', 'NA', 'نامشخص', '']) and \
           (not event_location_name or event_location_name in ['Unknown', 'NA', 'نامشخص', '']):
            return None, None
        
        # SPECIAL CASE: If arena_name contains broad indicators
        broad_indicators = ['های مختلف', 'مختلف', 'شهرهای', 'تمامی', 'همه', 'تمام']
        if any(word in arena_name for word in broad_indicators):
            # Try to use just the city if available
            if event_location_name and event_location_name not in ['Unknown', 'NA', 'نامشخص', '']:
                result = self._get_city_coords(event_location_name)
                if result:
                    return result['lat'], result['lng']
            return None, None
        
        # SPECIAL CASE: If arena_name == event_location_name (no specific location provided)
        # Try to use just the city name
        if arena_name == event_location_name and event_location_name:
            result = self._get_city_coords(event_location_name)
            if result:
                return result['lat'], result['lng']
        
        # Build combined location string
        location_parts = []
        
        # Add arena_name first (specific location)
        if arena_name and arena_name not in ['Unknown', 'NA', 'نامشخص', '']:
            location_parts.append(arena_name)
        
        # Add event_location_name (city) - only if different from arena_name
        if event_location_name and event_location_name not in ['Unknown', 'NA', 'نامشخص', ''] and event_location_name != arena_name:
            location_parts.append(event_location_name)
        
        # Always add country for context
        location_parts.append("ایران")
        
        # Join with commas
        location_string = ", ".join(location_parts)
        
        # Check cache using the full location string
        cached = self.cache.get(location_string)
        if cached:
            return cached.get('lat'), cached.get('lng')
        
        # Try city-only fallback first (faster and more reliable)
        if event_location_name and event_location_name not in ['Unknown', 'NA', 'نامشخص', '']:
            city_result = self._get_city_coords(event_location_name)
            if city_result:
                # Cache the result for the combined location too
                self.cache.set(location_string, city_result)
                return city_result['lat'], city_result['lng']
        
        try:
            # Try different search strategies
            search_queries = [
                location_string,  # Full location with country
                f"{arena_name}, ایران",  # Just arena + country
            ]
            
            # Only add city-only if we have a city
            if event_location_name and event_location_name not in ['Unknown', 'NA', 'نامشخص', '']:
                search_queries.append(f"{event_location_name}, ایران")
            
            # Remove duplicates and empty queries
            search_queries = [q for q in search_queries if q and len(q) > 3]
            search_queries = list(dict.fromkeys(search_queries))  # Remove duplicates
            
            for query in search_queries:
                params = {
                    'q': query,
                    'format': 'json',
                    'limit': 1,
                    'addressdetails': 1
                }
                headers = {'User-Agent': self.user_agent}
                
                response = requests.get(self.base_url, params=params, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        lat = float(results[0]['lat'])
                        lng = float(results[0]['lon'])
                        self.cache.set(location_string, {'lat': lat, 'lng': lng})
                        return lat, lng
                elif response.status_code == 429:
                    # Rate limited - wait and retry
                    time.sleep(2)
                    continue
            
            # If no results, try fuzzy matching for common locations
            result = self._fuzzy_geocode(arena_name, event_location_name)
            if result:
                self.cache.set(location_string, result)
                return result['lat'], result['lng']
            
            # Cache failure
            self.cache.set(location_string, None)
            return None, None
            
        except Exception as e:
            print(f"⚠️ Geocoding error for '{location_string}': {e}")
            return None, None
    
    def _get_city_coords(self, city_name: str) -> Optional[Dict]:
        """Get coordinates for a city from the internal dictionary."""
        if not city_name:
            return None
        
        city_name = city_name.strip()
        
        # Direct match
        if city_name in self.city_coords:
            return self.city_coords[city_name]
        
        # Try to find city by partial match
        for city, coords in self.city_coords.items():
            if city in city_name or city_name in city:
                return coords
        
        return None
    
    def _fuzzy_geocode(self, arena_name: str, event_location_name: str) -> Optional[Dict]:
        """Fallback fuzzy matching for common Iranian locations."""
        
        # If we only have a city (arena is empty), check city first
        if not arena_name or arena_name in ['Unknown', 'NA', 'نامشخص', '']:
            if event_location_name in self.city_coords:
                return self.city_coords[event_location_name]
        
        # Check if event_location_name is a known city
        if event_location_name in self.city_coords:
            return self.city_coords[event_location_name]
        
        # Try to find city in arena_name
        for city, coords in self.city_coords.items():
            if city in arena_name:
                return coords
        
        return None


# ============================================================
# DATA PREPARATION FUNCTIONS
# ============================================================

def find_files(directory: Path) -> list:
    """Find all Excel and CSV files in the directory, excluding temporary files"""
    files = []
    # Excel files (exclude temporary ~$ files)
    for f in directory.glob('*.xlsx'):
        if not f.name.startswith('~$'):
            files.append(f)
    for f in directory.glob('*.xls'):
        if not f.name.startswith('~$'):
            files.append(f)
    # CSV files
    files.extend(directory.glob('*.csv'))
    return files


def load_file(file_path: Path) -> pd.DataFrame:
    """Load a file based on its extension"""
    if file_path.suffix in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    elif file_path.suffix == '.csv':
        return pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path.suffix}")


def merge_files(files: list) -> pd.DataFrame:
    """Merge all files into a single DataFrame"""
    dfs = []
    
    print(f"\n📁 Found {len(files)} files:")
    for file in files:
        print(f"   - {file.name}")
    
    for file in files:
        try:
            df = load_file(file)
            dfs.append(df)
            print(f"   ✅ Loaded: {file.name} ({len(df)} rows)")
        except Exception as e:
            print(f"   ❌ Error loading {file.name}: {e}")
    
    if not dfs:
        print("❌ No files could be loaded")
        return pd.DataFrame()
    
    # Merge all DataFrames
    merged_df = pd.concat(dfs, ignore_index=True)
    print(f"\n📊 Merged: {len(merged_df)} total rows")
    
    return merged_df


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names for better readability"""
    # Remove leading/trailing spaces
    df.columns = df.columns.str.strip()
    
    # Handle unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Handle duplicate column names by renaming
    cols = df.columns.tolist()
    seen = {}
    new_cols = []
    for col in cols:
        if col in seen:
            seen[col] += 1
            new_cols.append(f"{col}_{seen[col]}")
        else:
            seen[col] = 0
            new_cols.append(col)
    df.columns = new_cols
    
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove rows where duplicate == 'Yes'
    Also remove exact duplicates based on id
    """
    original_count = len(df)
    
    # Remove rows where duplicate == 'Yes'
    if 'duplicate' in df.columns:
        df = df[df['duplicate'] != 'Yes']
        print(f"   🔄 Removed rows with duplicate = Yes: {original_count - len(df)} rows")
    
    # Remove exact duplicates based on id (keep first)
    if 'id' in df.columns:
        before = len(df)
        df = df.drop_duplicates(subset=['id'], keep='first')
        print(f"   🔄 Removed exact duplicates: {before - len(df)} rows")
    
    print(f"   ✅ Final rows: {len(df)}")
    return df


def geocode_locations(df: pd.DataFrame, geocoder: Geocoder) -> pd.DataFrame:
    """
    Geocode using both arena_name and event_location_name
    """
    # Convert columns to string to handle NaN
    df['arena_name'] = df['arena_name'].fillna('').astype(str)
    df['event_location_name'] = df['event_location_name'].fillna('').astype(str)
    
    # Create a combined location string for display
    df['location_for_geocoding'] = df.apply(
        lambda row: f"{row.get('arena_name', '')}, {row.get('event_location_name', '')}".strip(', '),
        axis=1
    )
    
    # Filter out empty/Unknown values
    valid_mask = ~df['location_for_geocoding'].isin(['', ',', 'Unknown, Unknown', 'NA, NA'])
    df_valid = df[valid_mask].copy()
    
    print(f"\n📍 Geocoding {len(df_valid)} locations...")
    
    # Create dictionaries for lat/lng
    lat_dict = {}
    lng_dict = {}
    
    # Use tqdm for progress bar
    for idx, row in tqdm(df_valid.iterrows(), total=len(df_valid), desc="Geocoding"):
        arena_name = row.get('arena_name', '')
        event_location_name = row.get('event_location_name', '')
        
        lat, lng = geocoder.geocode(arena_name, event_location_name)
        
        # Store by index
        lat_dict[idx] = lat
        lng_dict[idx] = lng
        
        # Rate limiting - Nominatim requires at least 1 second between requests
        time.sleep(1.1)
    
    # Add coordinates to dataframe
    df['lat'] = df.index.map(lat_dict)
    df['lng'] = df.index.map(lng_dict)
    
    # Count successful geocodes
    success_count = df['lat'].notna().sum()
    total_count = len(df)
    print(f"\n   ✅ Geocoded {success_count}/{total_count} rows ({success_count/total_count*100:.1f}%)")
    
    # Drop the temporary column
    df = df.drop(columns=['location_for_geocoding'])
    
    return df


def prepare_final_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare the final DataFrame for visualization"""
    
    # Define columns we want to keep
    keep_columns = [
        'id', 'title', 'date', 'event_date', 
        'event_location_name', 'arena_name', 'arena_type', 
        'protests_categories', 'protest_ritual', 'violent', 
        'protest_form_en', 'protest_form_fa',
        'issue', 'issue_specific', 'local_national_international',
        'issue_location_name', 'location_category',
        'target', 'organizer_type', 'civil_society_sector',
        'main_political_sector', 'size_of_participants',
        'is_multi_day', 'date_range_start', 'date_range_end', 'days_duration',
        'lat', 'lng', 'duplicate'
    ]
    
    # Keep only columns that exist
    existing_columns = [col for col in keep_columns if col in df.columns]
    final_df = df[existing_columns].copy()
    
    # Remove rows with no location data
    final_df = final_df[final_df['lat'].notna() & final_df['lng'].notna()]
    
    # Remove any duplicate columns that might have been created
    final_df = final_df.loc[:, ~final_df.columns.duplicated()]
    
    return final_df


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    """Main execution function"""
    
    print("="*60)
    print("📊 PROTEST DATA PREPARATION (FREE GEOCODING)")
    print("="*60)
    
    # 1. Find all files
    print("\n📁 Searching for files in:", PROCESSED_DIR)
    files = find_files(PROCESSED_DIR)
    
    if not files:
        print("❌ No files found in data/processed/")
        print("   Please make sure you have processed data files in:", PROCESSED_DIR)
        return
    
    # 2. Merge files
    print("\n🔄 Step 1: Merging files...")
    merged_df = merge_files(files)
    
    if merged_df.empty:
        print("❌ No data could be merged")
        return
    
    # 3. Clean column names
    print("\n🧹 Step 2: Cleaning column names...")
    merged_df = clean_column_names(merged_df)
    print(f"   ✅ Columns: {merged_df.columns.tolist()}")
    
    # 4. Remove duplicates
    print("\n🔍 Step 3: Removing duplicates...")
    merged_df = remove_duplicates(merged_df)
    
    # 5. Geocode locations (using free Nominatim)
    print("\n📍 Step 4: Geocoding locations...")
    print("   Using free Nominatim (OpenStreetMap) API")
    geocoder = Geocoder()
    merged_df = geocode_locations(merged_df, geocoder)
    
    # 6. Prepare final data
    print("\n📊 Step 5: Preparing final data...")
    final_df = prepare_final_data(merged_df)
    
    # 7. Save final data
    print("\n💾 Step 6: Saving final data...")
    
    # Save as CSV (faster loading)
    csv_output = OUTPUT_DIR / 'protests_for_dashboard.csv'
    final_df.to_csv(csv_output, index=False, encoding='utf-8-sig')
    print(f"   ✅ CSV saved: {csv_output}")
    
    # Save as Excel (more compatible)
    excel_output = OUTPUT_DIR / 'protests_for_dashboard.xlsx'
    final_df.to_excel(excel_output, index=False)
    print(f"   ✅ Excel saved: {excel_output}")
    
    # Save geocode cache stats
    cache_stats = {
        'total_locations': len(geocoder.cache.cache),
        'successful_geocodes': sum(1 for v in geocoder.cache.cache.values() if v is not None),
        'failed_geocodes': sum(1 for v in geocoder.cache.cache.values() if v is None)
    }
    print(f"\n📊 Geocode Cache Stats:")
    print(f"   Total cached: {cache_stats['total_locations']}")
    print(f"   Successful: {cache_stats['successful_geocodes']}")
    print(f"   Failed: {cache_stats['failed_geocodes']}")
    
    # 8. Summary
    print("\n" + "="*60)
    print("📊 PREPARATION SUMMARY")
    print("="*60)
    print(f"   Files merged: {len(files)}")
    print(f"   Rows after merge: {len(merged_df)}")
    print(f"   Rows with coordinates: {final_df['lat'].notna().sum()}")
    print(f"   Final rows for dashboard: {len(final_df)}")
    print(f"\n   Output saved to: {OUTPUT_DIR}")
    print("="*60)
    print("✅ Data preparation complete!")


if __name__ == "__main__":
    main()