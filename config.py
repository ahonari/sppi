import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the protest coder"""
    
    # API Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    MODEL_NAME = os.getenv('MODEL_NAME', 'gpt-4-turbo-preview')
    TEMPERATURE = float(os.getenv('TEMPERATURE', '0.1'))
    MAX_TOKENS = int(os.getenv('MAX_TOKENS', '2000'))
    
    # Processing Settings
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', '5'))
    DELAY_BETWEEN_BATCHES = float(os.getenv('DELAY_BETWEEN_BATCHES', '1.0'))
    
    # File Paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / 'data'
    RAW_DIR = DATA_DIR / 'raw'
    PROCESSED_DIR = DATA_DIR / 'processed'
    
    # Ensure directories exist
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    
    # Duplicate detection thresholds
    DUPLICATE_TITLE_SIMILARITY = 0.85  # Fuzzy match threshold
    DUPLICATE_SAME_EVENT_THRESHOLD = 0.75  # Combined similarity threshold
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        return True