"""
Debug script to see what the LLM is actually returning
"""
import os
import json
from dotenv import load_dotenv
import openai

load_dotenv()

def debug_llm_response():
    """Test the LLM response without all the wrapper code"""
    
    client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    model = os.getenv('MODEL_NAME', 'gpt-4o-mini')
    
    # Simple test prompt
    prompt = """
You are a data coder. Return ONLY valid JSON.

Article: "کارگران فولاد در اهواز مقابل شرکت تجمع کردند"

Return this JSON:
{
  "relevance": "Yes",
  "protest_form_en": "public assembly",
  "issue": "Labour",
  "event_location_name": "اهواز"
}
"""
    
    print("="*60)
    print("DEBUG: Testing LLM Response")
    print("="*60)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a precise data coder. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        content = response.choices[0].message.content
        
        print(f"\n📝 Raw Response:")
        print("-"*40)
        print(repr(content))  # Shows special characters
        print("-"*40)
        print(f"\n📊 Response Type: {type(content)}")
        print(f"📊 Response Length: {len(content)}")
        
        # Try to parse
        try:
            data = json.loads(content)
            print(f"\n✅ Successfully parsed JSON:")
            print(json.dumps(data, ensure_ascii=False, indent=2))
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parse Error: {e}")
            print(f"   Position: {e.pos}")
            print(f"   Problem around: {content[max(0, e.pos-20):e.pos+20]}")
            
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    debug_llm_response()