import openai
import json
import time
import re
from typing import Dict, Optional, List, Tuple
from tqdm import tqdm
import pandas as pd
import hashlib

from config import Config
from prompts import get_relevance_prompt, get_coding_prompt


class ProtestCoder:
    """Main class for coding protest events using LLM"""
    
    def __init__(self):
        """Initialize the coder with configuration"""
        Config.validate()
        
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.model = Config.MODEL_NAME
        self.temperature = Config.TEMPERATURE
        self.max_tokens = Config.MAX_TOKENS
        self.relevance_prompt = get_relevance_prompt()
        self.coding_prompt = get_coding_prompt()
        
        print(f"✅ Initialized ProtestCoder with model: {self.model}")
    
    def _get_llm_response(self, prompt: str, system_message: str = "You are a precise data coder.") -> Dict:
        """Get JSON response from LLM"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON parsing error: {e}")
            return {'_error': f'JSON parsing error: {str(e)}'}
        except Exception as e:
            print(f"⚠️ API error: {e}")
            return {'_error': str(e)}
    
    def check_relevance(self, title: str, subtitle: str) -> Tuple[bool, str]:
        """
        Stage 1: Check if article is relevant using only title and subtitle.
        Returns: (is_relevant, reason)
        """
        prompt = self.relevance_prompt.format(
            title=title or '',
            sub_title=subtitle or ''
        )
        
        result = self._get_llm_response(prompt)
        
        if result.get('_error'):
            print(f"⚠️ Error checking relevance: {result['_error']}")
            return False, f"Error: {result['_error']}"
        
        is_relevant = result.get('relevance') == 'Yes'
        reason = result.get('reason', 'No reason provided')
        
        return is_relevant, reason
    
    def code_article(self, row: pd.Series) -> Dict:
        """
        Stage 2: Full coding of a relevant article
        """
        prompt = self.coding_prompt.format(
            title=row.get('title', ''),
            sub_title=row.get('sub_title', ''),
            date=row.get('date', ''),
            summary=row.get('summary', ''),
            body=row.get('body', ''),
            service=row.get('service', ''),
            category=row.get('category', ''),
            tag=row.get('tag', '')
        )
        
        result = self._get_llm_response(prompt)
        
        # Ensure duplicate detection works properly
        if result.get('duplicate') == 'Yes':
            # If duplicate, make sure all other fields are null
            coding_fields = [
                'protest_ritual', 'violent', 'protest_form_en', 'protest_form_fa',
                'issue', 'issue_specific', 'local_national_international',
                'issue_location_name', 'location_category', 'target', 'organizer_type',
                'civil_society_sector', 'main_political_sector', 'event_location_name',
                'size_of_participants', 'arena_type', 'event_date',
                'is_multi_day', 'date_range_start', 'date_range_end', 'days_duration'
            ]
            for field in coding_fields:
                result[field] = None
        
        # Check for multi-day events
        is_multi_day, date_range = self._detect_multi_day(row)
        if is_multi_day and result.get('duplicate') != 'Yes':
            result['is_multi_day'] = 'Yes'
            if date_range:
                result['date_range_start'] = date_range.get('start', '')
                result['date_range_end'] = date_range.get('end', '')
            # Estimate duration
            result['days_duration'] = self._estimate_duration(row, date_range)
        
        # Add metadata
        result['_processing_status'] = 'success'
        result['_model_used'] = self.model
        
        return result
    
    def _detect_multi_day(self, row: pd.Series) -> Tuple[bool, Dict]:
        """
        Detect if article describes protests over multiple days.
        Returns: (is_multi_day, date_range_dict)
        """
        text = f"{row.get('title', '')} {row.get('sub_title', '')} {row.get('summary', '')} {row.get('body', '')}"
        
        patterns = [
            r'روز\s*(\d+)\s*و\s*(\d+)\s*[ام]?',
            r'دو\s*روز',
            r'سه\s*روز',
            r'چند\s*روز',
            r'برای\s*دومین\s*روز',
            r'برای\s*سومین\s*روز',
            r'از\s*دیروز',
            r'تا\s*امروز',
            r'سه\s*روزه',
            r'دومین\s*روز',
            r'سومین\s*روز',
        ]
        
        for pattern in patterns:
            if re.search(pattern, text):
                return True, {'start': row.get('date', ''), 'end': row.get('date', '')}
        
        return False, None
    
    def _estimate_duration(self, row: pd.Series, date_range: Dict) -> int:
        """Estimate the number of days for a multi-day event"""
        text = f"{row.get('title', '')} {row.get('sub_title', '')} {row.get('summary', '')} {row.get('body', '')}"
        
        patterns = [
            (r'(\d+)\s*روز', 1),
            (r'دو\s*روز', 2),
            (r'سه\s*روز', 3),
            (r'چهار\s*روز', 4),
            (r'پنج\s*روز', 5),
            (r'شش\s*روز', 6),
            (r'هفت\s*روز', 7),
            (r'چند\s*روز', 3),
        ]
        
        for pattern, days in patterns:
            if re.search(pattern, text):
                return days
        
        return 2
    
    def process_article(self, row: pd.Series) -> List[Dict]:
        """
        Complete processing pipeline for one article.
        Returns list of coded events.
        """
        # Stage 1: Check relevance using only title and subtitle
        title = row.get('title', '')
        subtitle = row.get('sub_title', '')
        
        is_relevant, reason = self.check_relevance(title, subtitle)
        
        if not is_relevant:
            return []
        
        # Stage 2: Full coding
        coded_result = self.code_article(row)
        
        # Check if it's a duplicate
        if coded_result.get('duplicate') == 'Yes':
            return [coded_result]
        
        # Check if multi-day event needs expansion
        if coded_result.get('is_multi_day') == 'Yes':
            return self._expand_multi_day_events(row, coded_result)
        else:
            return [coded_result]
    
    def _expand_multi_day_events(self, row: pd.Series, coded_data: Dict) -> List[Dict]:
        """Expand a multi-day event into separate rows for each day."""
        expanded_events = []
        num_days = coded_data.get('days_duration', 2)
        
        for day in range(1, num_days + 1):
            event_copy = coded_data.copy()
            event_copy['event_day'] = day
            event_copy['original_article_id'] = row.get('id', '')
            event_copy['_is_expanded'] = 'Yes'
            event_copy['_processing_status'] = 'success'
            event_copy['_model_used'] = self.model
            event_copy['duplicate'] = 'No'
            expanded_events.append(event_copy)
        
        return expanded_events
    
    def process_batch(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process a batch of articles."""
        all_results = []
        
        with tqdm(total=len(df), desc="Processing articles") as pbar:
            for idx, row in df.iterrows():
                coded_events = self.process_article(row)
                
                for event in coded_events:
                    combined = row.to_dict()
                    combined.update(event)
                    all_results.append(combined)
                
                pbar.update(1)
                
                if (idx + 1) % Config.BATCH_SIZE == 0 and (idx + 1) < len(df):
                    time.sleep(Config.DELAY_BETWEEN_BATCHES)
        
        result_df = pd.DataFrame(all_results)
        
        if not result_df.empty and 'relevance' in result_df.columns:
            result_df = result_df[result_df['relevance'] != 'No']
        
        if not result_df.empty:
            relevant_count = len(result_df[result_df.get('relevance') == 'Yes'])
            duplicate_count = len(result_df[result_df.get('duplicate') == 'Yes'])
            expanded_count = len(result_df[result_df.get('_is_expanded') == 'Yes'])
            
            print(f"\n📊 Processing Summary:")
            print(f"   📰 Total articles processed: {len(df)}")
            print(f"   ✅ Relevant events: {relevant_count}")
            print(f"   🔄 Duplicates identified: {duplicate_count}")
            print(f"   📅 Expanded multi-day events: {expanded_count}")
        else:
            print(f"\n📊 Processing Summary:")
            print(f"   📰 Total articles processed: {len(df)}")
            print(f"   ⚠️  No relevant events found")
        
        return result_df


class DuplicateDetector:
    """Detect duplicate articles and group by event"""
    
    def __init__(self):
        self.duplicates = {}
    
    def _create_event_signature(self, row: pd.Series) -> str:
        """Create a signature for an event based on key fields."""
        if row.get('duplicate') == 'Yes':
            return ''
        
        fields = [
            'issue_location_name', 'event_location_name', 'protest_form_en',
            'issue', 'target', 'size_of_participants'
        ]
        
        signature_parts = []
        for field in fields:
            value = str(row.get(field, ''))
            if value and value not in ['NA', 'Unknown', 'None', '']:
                signature_parts.append(value)
        
        signature_parts.sort()
        signature = '|'.join(signature_parts)
        
        date = row.get('date', '')
        if date:
            signature = f"{date}|{signature}"
        
        return hashlib.md5(signature.encode('utf-8')).hexdigest() if signature else ''
    
    def detect_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect duplicate events in the coded DataFrame."""
        relevant_df = df[df.get('relevance') == 'Yes'].copy()
        
        if relevant_df.empty:
            return df
        
        relevant_df['_signature'] = relevant_df.apply(self._create_event_signature, axis=1)
        signature_groups = relevant_df[relevant_df['_signature'] != ''].groupby('_signature').size()
        duplicate_groups = signature_groups[signature_groups > 1].index
        
        duplicate_map = {}
        for sig in duplicate_groups:
            group_events = relevant_df[relevant_df['_signature'] == sig]
            group_id = hashlib.md5(sig.encode('utf-8')).hexdigest()
            
            for idx, row in group_events.iterrows():
                duplicate_map[idx] = {
                    'group_id': group_id,
                    'is_duplicate': 'Yes' if idx != group_events.index[0] else 'No'
                }
        
        for idx, info in duplicate_map.items():
            if df.loc[idx, 'duplicate'] != 'Yes':
                df.loc[idx, 'duplicate'] = info['is_duplicate']
                df.loc[idx, 'duplicate_group_id'] = info['group_id']
            
            if info['is_duplicate'] == 'Yes':
                coding_fields = [
                    'protest_ritual', 'violent', 'protest_form_en', 'protest_form_fa',
                    'issue', 'issue_specific', 'local_national_international',
                    'issue_location_name', 'location_category', 'target', 'organizer_type',
                    'civil_society_sector', 'main_political_sector', 'event_location_name',
                    'size_of_participants', 'arena_type', 'event_date',
                    'is_multi_day', 'date_range_start', 'date_range_end', 'days_duration'
                ]
                for field in coding_fields:
                    if field in df.columns:
                        df.loc[idx, field] = None
        
        duplicate_count = len(df[df['duplicate'] == 'Yes'])
        print(f"   🔄 Duplicates detected: {duplicate_count} duplicate events")
        
        return df


class ProtestCoderTest:
    """Test class for testing the coder"""
    
    @staticmethod
    def get_test_data():
        """Return sample test data"""
        return pd.DataFrame([
            {
                'id': 1,
                'title': 'تجمع اعتراضی کارگران فولاد در اهواز',
                'sub_title': 'کارگران خواستار پرداخت معوقات خود شدند',
                'date': '1402/10/15',
                'persian_date': '۱۵ دی ۱۴۰۲',
                'url': 'https://example.com/news/1',
                'summary': 'جمعی از کارگران شرکت فولاد اهواز امروز در مقابل ساختمان این شرکت تجمع کردند.',
                'body': 'جمعی از کارگران شرکت فولاد اهواز امروز با تجمع در مقابل ساختمان مرکزی این شرکت، نسبت به عدم پرداخت حقوق خود اعتراض کردند. این تجمع حدود دو ساعت به طول انجامید و با حضور حدود ۲۰۰ نفر از کارگران همراه بود.',
                'service': 'ایرنا',
                'category': 'اجتماعی',
                'tag': 'کارگری, اعتراضات, اهواز'
            },
            {
                'id': 2,
                'title': 'دومین روز اعتصاب کارگران فولاد در اهواز',
                'sub_title': 'اعتصاب کارگران برای دومین روز ادامه دارد',
                'date': '1402/10/16',
                'persian_date': '۱۶ دی ۱۴۰۲',
                'url': 'https://example.com/news/2',
                'summary': 'کارگران فولاد اهواز برای دومین روز متوالی اعتصاب کردند.',
                'body': 'کارگران شرکت فولاد اهواز برای دومین روز متوالی با تجمع در مقابل این شرکت، خواستار پرداخت حقوق معوقه خود شدند. این اعتصاب از دیروز آغاز شده است.',
                'service': 'ایرنا',
                'category': 'اجتماعی',
                'tag': 'کارگری, اعتصاب, اهواز'
            },
            {
                'id': 3,
                'title': 'تظاهرات دانشجویان در تهران',
                'sub_title': 'دانشجویان خواستار آزادی زندانیان سیاسی شدند',
                'date': '1402/11/20',
                'persian_date': '۲۰ بهمن ۱۴۰۲',
                'url': 'https://example.com/news/3',
                'summary': 'دانشجویان دانشگاه تهران امروز در محوطه دانشگاه تجمع کردند.',
                'body': 'جمعی از دانشجویان دانشگاه تهران امروز با تجمع در محوطه این دانشگاه، خواستار آزادی فوری زندانیان سیاسی شدند. این تجمع با حضور حدود ۵۰۰ نفر از دانشجویان برگزار شد.',
                'service': 'خبرگزاری دانشجو',
                'category': 'سیاسی',
                'tag': 'دانشجویی, اعتراضات, تهران'
            },
            {
                'id': 4,
                'title': 'اعتراضات در خارج از ایران: تجمع ایرانیان در برلین',
                'sub_title': 'ایرانیان مقیم آلمان در برلین تجمع کردند',
                'date': '1402/11/22',
                'persian_date': '۲۲ بهمن ۱۴۰۲',
                'url': 'https://example.com/news/4',
                'summary': 'جمعی از ایرانیان مقیم آلمان در برلین تجمع کردند.',
                'body': 'جمعی از ایرانیان مقیم آلمان با تجمع در مقابل سفارت ایران در برلین، خواستار آزادی زندانیان سیاسی شدند.',
                'service': 'رادیو فردا',
                'category': 'سیاسی',
                'tag': 'ایرانیان خارج, اعتراضات, برلین'
            },
            {
                'id': 5,
                'title': 'تحلیل اعتراضات اخیر کارگری در ایران',
                'sub_title': 'یک کارشناس مسائل کارگری به بررسی دلایل اعتراضات پرداخت',
                'date': '1402/11/23',
                'persian_date': '۲۳ بهمن ۱۴۰۲',
                'url': 'https://example.com/news/5',
                'summary': 'یک تحلیل از اعتراضات کارگری اخیر در ایران.',
                'body': 'در این گفتگو، یک کارشناس مسائل کارگری به تحلیل دلایل اعتراضات اخیر کارگران در ایران پرداخت و راهکارهایی را ارائه کرد.',
                'service': 'خبرگزاری مهر',
                'category': 'تحلیل',
                'tag': 'تحلیل, کارگری'
            },
            {
                'id': 6,
                'title': 'تجمع کارگران فولاد در اهواز (تکرار)',
                'sub_title': 'کارگران فولاد خواستار حقوق خود شدند',
                'date': '1402/10/15',
                'persian_date': '۱۵ دی ۱۴۰۲',
                'url': 'https://example.com/news/6',
                'summary': 'کارگران فولاد اهواز در مقابل شرکت تجمع کردند.',
                'body': 'کارگران شرکت فولاد اهواز امروز با تجمع در مقابل ساختمان این شرکت اعتراض کردند.',
                'service': 'خبرگزاری مهر',
                'category': 'اجتماعی',
                'tag': 'کارگری, اهواز'
            }
        ])
    
    @staticmethod
    def run_test():
        """Run a complete test"""
        print("="*60)
        print("🧪 RUNNING COMPREHENSIVE TEST")
        print("="*60)
        
        test_df = ProtestCoderTest.get_test_data()
        print(f"\n📄 Test data: {len(test_df)} articles")
        
        print("\n📋 Test articles:")
        for idx, row in test_df.iterrows():
            print(f"   {idx+1}. {row['title']}")
        
        coder = ProtestCoder()
        
        print("\n🔄 Processing test articles...")
        results = coder.process_batch(test_df)
        
        if not results.empty:
            print("\n🔍 Detecting duplicates...")
            detector = DuplicateDetector()
            results = detector.detect_duplicates(results)
        
        print("\n📋 CODING RESULTS:")
        print("="*60)
        
        if results.empty:
            print("⚠️ No relevant events found")
            return results
        
        for idx, row in results.iterrows():
            print(f"\n📰 Article: {row.get('title', 'No title')[:50]}...")
            print(f"   ID: {row.get('id', 'N/A')}")
            
            if row.get('relevance') == 'Yes':
                is_duplicate = row.get('duplicate') == 'Yes'
                print(f"   🔄 Duplicate: {is_duplicate}")
                
                if is_duplicate:
                    print(f"   ⚠️  DUPLICATE - No coding fields filled")
                else:
                    print(f"   ✅ Form: {row.get('protest_form_en', 'Unknown')}")
                    print(f"   ✅ Issue: {row.get('issue', 'Unknown')}")
                    print(f"   ✅ Location: {row.get('event_location_name', 'Unknown')}")
                    if row.get('_is_expanded') == 'Yes':
                        print(f"   📅 Day: {row.get('event_day', 'N/A')} of {row.get('days_duration', 'N/A')}")
            else:
                print(f"   ⏭️  Skipped (irrelevant)")
        
        print("\n" + "="*60)
        print("✅ Test completed!")
        return results