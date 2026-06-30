# prompts.py

def get_relevance_prompt() -> str:
    """Return the relevance screening prompt (only reads title + subtitle)"""
    return """
You are an expert screener for protest events in Iran.

## TASK | وظیفه
Analyze the article title and subtitle to determine if this article should be coded as a protest event inside Iran.

## RULES | قوانین
1. **RELEVANT (Yes)** if the article reports a protest/event that took place INSIDE Iran
2. **NOT RELEVANT (No)** if:
   - The event is OUTSIDE Iran (even if it's about Iranians or Iranian issues)
   - The article is an analysis/opinion piece, not reporting an actual event
   - The article is about protests in other countries
   - The article is about Iranian protests abroad (e.g., diaspora protests in Europe, US, etc.)
   - There is no actual protest event mentioned (just discussion/analysis)

## EXAMPLES | مثال‌ها
- ✅ "تجمع کارگران فولاد در اهواز" -> Yes (inside Iran)
- ✅ "تظاهرات دانشجویان در تهران" -> Yes (inside Iran)
- ❌ "تجمع ایرانیان مقیم آلمان در برلین" -> No (outside Iran)
- ❌ "تحلیل اعتراضات اخیر در ایران" -> No (analysis, not an event)
- ❌ "واکنش ایران به اعتراضات در عراق" -> No (outside Iran, not a protest event inside Iran)

## INPUT
Title (عنوان): {title}
Subtitle (زیرعنوان): {sub_title}

## OUTPUT
Return ONLY JSON with these keys:
{{
  "relevance": "Yes",  // or "No"
  "reason": "Brief explanation in English why this is relevant/not relevant"
}}
"""


def get_coding_prompt() -> str:
    """Return the full coding prompt (used only for relevant articles)"""
    return """
You are an expert coder for protest events in Iran.

## IMPORTANT INSTRUCTIONS | دستورالعمل‌های مهم

1. **This article has been confirmed as relevant** (event inside Iran)
2. Read the article in this order: **Title → Subtitle → Summary → Body**
3. Once you find all the information needed, STOP reading further (do not read the body if you already have all info from title, subtitle, and summary)
4. **IMPORTANT: If this appears to be a duplicate report of the same event** (another article covering the same protest), set `duplicate = "Yes"` and leave ALL other coding fields empty/null
5. **If NOT a duplicate**, code all fields with the appropriate values
6. **Multi-day events**: If the article mentions protests over multiple days, flag `is_multi_day = "Yes"` and provide the date range
7. **Do NOT code events outside Iran** (relevance already filtered)
8. **Do NOT code analysis or opinion pieces** (relevance already filtered)

## RULES FOR DUPLICATE DETECTION
A report is a **DUPLICATE** if:
- It covers the same protest event as another article
- Same location, same date/period, same target, same issue
- Example: Two different news agencies reporting on the same protest in Tehran on the same day

If duplicate = "Yes", the output should look like:
{{
  "relevance": "Yes",
  "duplicate": "Yes",
  "protest_form_en": null,
  "protest_form_fa": null,
  "issue": null,
  "issue_specific": null,
  "local_national_international": null,
  "issue_location_name": null,
  "location_category": null,
  "target": null,
  "organizer_type": null,
  "civil_society_sector": null,
  "main_political_sector": null,
  "event_location_name": null,
  "size_of_participants": null,
  "arena_type": null,
  "event_date": null,
  "is_multi_day": "No",
  "date_range_start": null,
  "date_range_end": null,
  "days_duration": null
}}

## ARTICLE INFORMATION
Title (عنوان): {title}
Subtitle (زیرعنوان): {sub_title}
Date (تاریخ): {date}
Summary (خلاصه): {summary}
Body (متن کامل): {body}
Service (منبع): {service}
Category (دسته‌بندی): {category}
Tags (برچسب‌ها): {tag}

## CODEBOOK (Only fill these if duplicate = "No")

### Basic Information
- **Protest_Ritual**: 'Protest' (اعتراض), 'Ritual' (مراسم/آیین), 'Armed Conflicts' (درگیری مسلحانه)
- **Violent**: 'YES', 'NO', or 'Unknown'

### Protest Forms (Choose ONE)
**Petitioning:**
- 'Civil campaigning' (کمپین مدنی یا پویشگری)
- 'Collective open letter' (نامه جمعی اعتراضی)
- 'Contacting politicians, officials, parliament members, media etc.' (تماس با سیاستمداران و مسئولان و رسانه‌ها)
- 'Petitionning' (طومار نویسی)

**Demonstrative protests (legal and nonviolent):**
- 'demonstration (legal and non-violent)' (تظاهرات)
- 'march/ rally' (راهپیمایی)
- 'public assembly' (تجمع / اجتماع)
- 'electoral assembly' (تجمع انتخاباتی)
- 'vigil' (تحصن)
- 'symbolic demonstrations' (اعتراضات نمادین)

**Confrontational protests (illegal and non violent):**
- 'blockade' (بلوک کردن مسیر)
- 'boycott' (تحریم)
- 'disturbance of meetings' (اخلال در مراسم)
- 'Hacking' (هک کردن)
- 'illegal demonstration (if non-violent)' (تظاهرات بدون مجوز)
- 'limited destruction of property' (آسیب محدود به اموال)
- 'occupation' (اشغال مکان یا ساختمان حکومتی)
- 'picket' (راهبندان، سد معبر)
- 'sabotage' (خرابکاری عمدی)
- 'self-mutilation (e.g., hunger strike, suicide)' (آسیب به خود)
- 'strike' (اعتصاب)
- 'symbolic violence' (خشونت نمادین)

**Violent protests:**
- 'violent demonstration' (تظاهرات خشونت آمیز)
- 'rioting' (شورش خیابانی)
- 'arson and other severe destruction' (آتش زدن)
- 'physical violence against people' (حمله به افراد)

**Armed conflict:**
- 'threats' (تهدید)
- 'armed attack' (حمله/درگیری مسلحانه)
- 'bombing' (بمب‌گذاری)
- 'Other' (سایر)

### Issue Categories
Choose ONE: 'Business', 'Children', 'Cultural', 'Disability', 'Economic', 'Environmental', 'Ethnic', 'Financial/banking', 'Human rights', 'International', 'Labour', 'Political', 'Religious', 'Social', 'Student/university', 'Urban', 'Women', 'Other', 'Unknown'

### Issue-Specific (Only if applicable)
- Environmental: 'Env_Air pollution', 'Env_Decrease biodiversity', 'Env_Deforestation', 'Env_Desertification', 'Env_Drought/ water scarcity', 'Env_Haze', 'Env_Industrial effluents', 'Env_Industrial pollution', 'Env_Soil Degradation', 'Env_Vehicle emissions', 'Env_Waste Disposal'
- International: 'Intl_Islamic', 'Int_Nuclear Technology', 'Intl_Palestine-Israel', 'Intl_Politics', 'Intl_Regional'
- Social: 'Soc_Addiction'
- Urban: 'Urb_City election', 'Urb_Cultural heritage', 'Urb_Drinking water pollution/scarcity', 'Urb_Green spaces', 'Urb_Homeless people', 'Urb_Informal settlers'
- Women: 'Wo_Hijab', 'Wo_Political participation'
- For others: 'N/A'

### Location & Scale
- **Local/National/International**: 'Local', 'National', 'International'
- **Location_Category**: 'Capital', 'Province Center', 'City', 'Town', 'Rural', 'National', 'NA'
- **size_of_participants**: 'small group < 15', 'medium group <50', 'Large Group <200', 'Mob < 1000', 'thousands, +1000', 'massive > 100,000', '1 group/organization', 'more than 1 group/organization', '1 person', 'unknown'

### Actors
- **target**: 'Conservatives', 'Government', 'International Institution/Country', 'Judiciary', 'Law Enforcement Force', 'Local authorities/agencies', 'Military base', 'Ministries', 'Municipality/ city councils', 'Non-governmental Organizations', 'Parliament', 'Political Party/Politician', 'Private Companies/organizations', 'Public Awareness', 'Reformists', 'State Companies/organizations', 'Supreme Leader', 'University Officials', 'Other', 'None', 'Unknown'
- **Organizer_type**: 'Armed/Separatist group', 'Campaign', 'Formal religious group', 'Formal student group', 'GONGO', 'Informal Group', 'Labour Union', 'NGO/Community', 'Online Community', 'Ordinary Citizens', 'Political Org. Outside Iran', 'Political Org./Party', 'Prayers', 'Syndicate', 'Other', 'Diverse', 'Unknown', 'None'
- **CivilSocietySector**: 'Animal rights', 'Charity', 'Children's rights', 'Cultural', 'Disability rights', 'Economic/trade/business', 'Environmental', 'Ethnic', 'Farmers', 'Human rights', 'Journalists', 'Labour', 'Lawyers', 'Nurses', 'Political', 'Religious', 'Retireds', 'Social', 'Student Movement', 'Teachers', 'Urban', 'Women', 'None', 'Other', 'Diverse', 'Unknown'
- **MainPoliticalSector**: 'Reformist', 'Progovernment', 'Conservative', 'Neutral', 'Other', 'Unknown'

### Event Arena
- **Arena_type**: 'In front of private companies', 'In front of state buildings', 'International office/ embassy', 'Municipality/ city councils', 'Online', 'Out of residential areas/ Roads', 'Parliament area', 'Prisons', 'Public place', 'Religious places', 'Streets', 'University campuses', 'Working places', 'Other', 'NA', 'Unknown'

## OUTPUT FORMAT
Return ONLY valid JSON with these keys:

### If NOT a duplicate (duplicate = "No"):
{{
  "relevance": "Yes",
  "duplicate": "No",
  "protest_ritual": "",
  "violent": "",
  "protest_form_en": "",
  "protest_form_fa": "",
  "issue": "",
  "issue_specific": "",
  "local_national_international": "",
  "issue_location_name": "",
  "location_category": "",
  "target": "",
  "organizer_type": "",
  "civil_society_sector": "",
  "main_political_sector": "",
  "event_location_name": "",
  "size_of_participants": "",
  "arena_type": "",
  "event_date": "",
  "is_multi_day": "No",
  "date_range_start": "",
  "date_range_end": "",
  "days_duration": 1
}}

### If duplicate = "Yes" (ALL other fields should be null):
{{
  "relevance": "Yes",
  "duplicate": "Yes",
  "protest_ritual": null,
  "violent": null,
  "protest_form_en": null,
  "protest_form_fa": null,
  "issue": null,
  "issue_specific": null,
  "local_national_international": null,
  "issue_location_name": null,
  "location_category": null,
  "target": null,
  "organizer_type": null,
  "civil_society_sector": null,
  "main_political_sector": null,
  "event_location_name": null,
  "size_of_participants": null,
  "arena_type": null,
  "event_date": null,
  "is_multi_day": "No",
  "date_range_start": null,
  "date_range_end": null,
  "days_duration": null
}}

IMPORTANT: 
- Location names should be in Persian as written in the article
- If duplicate = "Yes", leave ALL other fields as null
"""