"""
Quick Recovery Script - Merge all files without re-geocoding
Uses existing geocode cache and processed files
"""

import pandas as pd
import json
import time
import requests
from pathlib import Path
from typing import Dict, Optional, Tuple
from tqdm import tqdm

# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).parent.parent
PROCESSED_DIR = BASE_DIR / 'data' / 'processed'
OUTPUT_DIR = BASE_DIR / 'data' / 'dashboard'
GEOCODE_CACHE_FILE = BASE_DIR / 'data' / 'geocode_cache.json'

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# GEOCODE CACHE
# ============================================================

class GeocodeCache:
    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def get(self, location: str) -> Optional[Dict]:
        if location in self.cache:
            return self.cache[location]
        return None
    
    def set(self, location: str, result: Dict):
        self.cache[location] = result
        self._save_cache()


class Geocoder:
    def __init__(self):
        self.cache = GeocodeCache(GEOCODE_CACHE_FILE)
        self.user_agent = "ProtestDashboard/1.0"
        self.base_url = "https://nominatim.openstreetmap.org/search"
        
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
            'نکا': {'lat': 36.6500, 'lng': 53.3000},
            'آبادان': {'lat': 30.3390, 'lng': 48.3040},
            'خرمشهر': {'lat': 30.4400, 'lng': 48.1800},
            'دزفول': {'lat': 32.3830, 'lng': 48.4000},
            'گچساران': {'lat': 30.3500, 'lng': 50.8000},
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
        }
    
    def geocode(self, arena_name: str, event_location_name: str = None) -> Tuple[Optional[float], Optional[float]]:
        """Geocode a location - checks cache first, only calls API if not cached."""
        
        # Handle NaN
        if arena_name is None or (isinstance(arena_name, float) and pd.isna(arena_name)):
            arena_name = ''
        else:
            arena_name = str(arena_name).strip()
        
        if event_location_name is None or (isinstance(event_location_name, float) and pd.isna(event_location_name)):
            event_location_name = ''
        else:
            event_location_name = str(event_location_name).strip()
        
        # If both are empty, return None
        if (not arena_name or arena_name in ['Unknown', 'NA', 'نامشخص', '']) and \
           (not event_location_name or event_location_name in ['Unknown', 'NA', 'نامشخص', '']):
            return None, None
        
        # Build location string for cache lookup
        location_parts = []
        if arena_name and arena_name not in ['Unknown', 'NA', 'نامشخص', '']:
            location_parts.append(arena_name)
        if event_location_name and event_location_name not in ['Unknown', 'NA', 'نامشخص', ''] and event_location_name != arena_name:
            location_parts.append(event_location_name)
        location_parts.append("ایران")
        location_string = ", ".join(location_parts)
        
        # 1. CHECK CACHE FIRST
        cached = self.cache.get(location_string)
        if cached:
            return cached.get('lat'), cached.get('lng')
        
        # Also check without country
        location_string_no_country = ", ".join(location_parts[:-1])
        cached = self.cache.get(location_string_no_country)
        if cached:
            self.cache.set(location_string, cached)
            return cached.get('lat'), cached.get('lng')
        
        # 2. Try city fallback from dictionary
        if event_location_name and event_location_name in self.city_coords:
            coords = self.city_coords[event_location_name]
            self.cache.set(location_string, coords)
            return coords['lat'], coords['lng']
        
        # 3. Try Nominatim API (ONLY if not in cache)
        try:
            params = {'q': location_string, 'format': 'json', 'limit': 1}
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
                time.sleep(2)
                return self.geocode(arena_name, event_location_name)
        except Exception as e:
            print(f"⚠️ Geocoding error: {e}")
        
        # 4. Try fuzzy match
        for city, coords in self.city_coords.items():
            if city in arena_name:
                self.cache.set(location_string, coords)
                return coords['lat'], coords['lng']
        
        # 5. Cache failure
        self.cache.set(location_string, None)
        return None, None


# ============================================================
# FILE HANDLING
# ============================================================

def load_file(file_path: Path) -> pd.DataFrame:
    """Load a file based on its extension"""
    if file_path.suffix in ['.xlsx', '.xls']:
        return pd.read_excel(file_path)
    elif file_path.suffix == '.csv':
        return pd.read_csv(file_path)
    else:
        raise ValueError(f"Unsupported file: {file_path.suffix}")


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names"""
    df.columns = df.columns.str.strip()
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicates"""
    if 'duplicate' in df.columns:
        df = df[df['duplicate'] != 'Yes']
    if 'id' in df.columns:
        df = df.drop_duplicates(subset=['id'], keep='first')
    return df


def add_coordinates_from_cache_or_geocode(df: pd.DataFrame, geocoder: Geocoder) -> pd.DataFrame:
    """
    Add lat/lng - checks cache first, only geocodes if not cached.
    """
    print("\n📍 Adding coordinates from cache or geocoding...")
    
    # Convert to strings
    df['arena_name'] = df['arena_name'].fillna('').astype(str)
    df['event_location_name'] = df['event_location_name'].fillna('').astype(str)
    
    lat_list = []
    lng_list = []
    cached_count = 0
    geocoded_count = 0
    failed_count = 0
    
    # Count total rows
    total = len(df)
    
    for idx, row in tqdm(df.iterrows(), total=total, desc="Processing locations"):
        arena_name = row.get('arena_name', '')
        event_location_name = row.get('event_location_name', '')
        
        # Build location key
        parts = []
        if arena_name and arena_name not in ['Unknown', 'NA', 'نامشخص', '']:
            parts.append(arena_name)
        if event_location_name and event_location_name not in ['Unknown', 'NA', 'نامشخص', '']:
            parts.append(event_location_name)
        location_key = ", ".join(parts) if parts else ""
        
        # Check if in cache
        if location_key and geocoder.cache.get(location_key):
            cached = geocoder.cache.get(location_key)
            if cached:
                lat_list.append(cached.get('lat'))
                lng_list.append(cached.get('lng'))
                cached_count += 1
                continue
        
        # Not in cache - geocode
        lat, lng = geocoder.geocode(arena_name, event_location_name)
        if lat and lng:
            geocoded_count += 1
        else:
            failed_count += 1
        lat_list.append(lat)
        lng_list.append(lng)
    
    df['lat'] = lat_list
    df['lng'] = lng_list
    
    print(f"\n   ✅ Cache hits: {cached_count}")
    print(f"   ✅ New geocoded: {geocoded_count}")
    print(f"   ❌ Failed: {failed_count}")
    
    return df


def prepare_final_data(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare final data"""
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
    
    existing_columns = [col for col in keep_columns if col in df.columns]
    final_df = df[existing_columns].copy()
    final_df = final_df[final_df['lat'].notna() & final_df['lng'].notna()]
    final_df = final_df.loc[:, ~final_df.columns.duplicated()]
    
    return final_df


# ============================================================
# MAIN
# ============================================================

def main():
    print("="*60)
    print("📊 RECOVER DASHBOARD - NO GEOCODING")
    print("="*60)
    
    # 1. Load cache
    print("\n📂 Loading geocode cache...")
    cache = GeocodeCache(GEOCODE_CACHE_FILE)
    print(f"   ✅ Cache has {len(cache.cache)} entries")
    
    # 2. Find all files
    print("\n📁 Finding files in processed folder...")
    files = []
    for f in PROCESSED_DIR.glob('*.xlsx'):
        if not f.name.startswith('~$'):
            files.append(f)
    for f in PROCESSED_DIR.glob('*.csv'):
        files.append(f)
    
    if not files:
        print("❌ No files found in data/processed/")
        return
    
    print(f"   ✅ Found {len(files)} files")
    
    # 3. Load and merge all files
    print("\n🔄 Merging all files...")
    all_dfs = []
    total_rows = 0
    
    for f in files:
        try:
            df = load_file(f)
            all_dfs.append(df)
            total_rows += len(df)
            print(f"   ✅ Loaded: {f.name} ({len(df)} rows)")
        except Exception as e:
            print(f"   ❌ Error loading {f.name}: {e}")
    
    if not all_dfs:
        print("❌ No files could be loaded")
        return
    
    merged_df = pd.concat(all_dfs, ignore_index=True)
    print(f"\n   ✅ Merged: {len(merged_df)} total rows")
    
    # 4. Clean columns
    print("\n🧹 Cleaning columns...")
    merged_df = clean_column_names(merged_df)
    
    # 5. Remove duplicates
    print("\n🔍 Removing duplicates...")
    before = len(merged_df)
    merged_df = remove_duplicates(merged_df)
    print(f"   ✅ Removed {before - len(merged_df)} duplicates")
    print(f"   ✅ Final rows: {len(merged_df)}")
    
    # 6. Add coordinates (cache first, geocode only if missing)
    geocoder = Geocoder()
    merged_df = add_coordinates_from_cache_or_geocode(merged_df, geocoder)
    
    # 7. Prepare final data
    print("\n📊 Preparing final data...")
    final_df = prepare_final_data(merged_df)
    
    # 8. Save
    print("\n💾 Saving dashboard...")
    
    excel_path = OUTPUT_DIR / 'protests_for_dashboard.xlsx'
    final_df.to_excel(excel_path, index=False)
    print(f"   ✅ Excel saved: {excel_path}")
    
    csv_path = OUTPUT_DIR / 'protests_for_dashboard.csv'
    final_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    print(f"   ✅ CSV saved: {csv_path}")
    
    # Save updated cache
    geocoder.cache._save_cache()
    print(f"   ✅ Cache updated with new entries")
    
    # 9. Summary
    print("\n" + "="*60)
    print("📊 RECOVERY COMPLETE")
    print("="*60)
    print(f"   Files merged: {len(files)}")
    print(f"   Total rows: {len(merged_df)}")
    print(f"   Rows with coordinates: {final_df['lat'].notna().sum()}")
    print(f"   Final dashboard rows: {len(final_df)}")
    print(f"   Cache entries: {len(geocoder.cache.cache)}")
    print(f"\n   Output: {excel_path}")
    print("="*60)


if __name__ == "__main__":
    main()