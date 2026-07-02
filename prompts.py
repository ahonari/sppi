def get_coding_prompt() -> str:
    """Return the full coding prompt (used only for relevant articles)"""
    return """
You are an expert coder for protest events in Iran.

## IMPORTANT INSTRUCTIONS | دستورالعمل‌های مهم

1. **This article has been pre-classified as relevant** (event inside Iran)
2. Read the article in this order: **Title → Subtitle → Summary → Body**
3. **You MUST extract ALL available information** from the article
4. **If information is not explicitly mentioned**, use "Unknown" or leave empty
5. **For PROTEST FORMS**: Choose the MOST SPECIFIC form that matches the action
6. **For ISSUE**: Identify the MAIN issue/topic of the protest
7. **For TARGET**: Who is the protest directed against?
8. **For LOCATION**: Extract the specific location mentioned (city, region, building)
9. **For PARTICIPANTS**: Estimate the number if mentioned
10. **DUPLICATE**: Set to "Yes" ONLY if this is clearly a duplicate report of the SAME event from another source

## RULES FOR DUPLICATE DETECTION
A report is a DUPLICATE if:
- It covers the SAME protest event as another article
- Same location, same date/period, same target, same issue
- Example: Two different news agencies reporting on the same protest in Tehran on the same day
- **ONLY mark as duplicate if it's CLEARLY the same event**

## ARTICLE INFORMATION
Title (عنوان): {title}
Subtitle (زیرعنوان): {sub_title}
Date (تاریخ): {date}
Summary (خلاصه): {summary}
Body (متن کامل): {body}
Service (منبع): {service}
Category (دسته‌بندی): {category}
Tags (برچسب‌ها): {tag}

## CODEBOOK

### Basic Information
- **Protest_Ritual**: 'Protest' (اعتراض), 'Ritual' (مراسم/آیین), 'Armed Conflicts' (درگیری مسلحانه)
- **Violent**: 'YES', 'NO', or 'Unknown'

### Protest Forms (Choose ONE that BEST matches)
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

### Issue Categories (Choose ONE that BEST fits)
Choose ONE: 'Business', 'Children', 'Cultural', 'Disability', 'Economic', 'Environmental', 'Ethnic', 'Financial/banking', 'Human rights', 'International', 'Labour', 'Political', 'Religious', 'Social', 'Student/university', 'Urban', 'Women', 'Other', 'Unknown'

### Issue-Specific (Only if applicable - otherwise use 'N/A')
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
- **target** (who is the protest directed against): 'Conservatives', 'Government', 'International Institution/Country', 'Judiciary', 'Law Enforcement Force', 'Local authorities/agencies', 'Military base', 'Ministries', 'Municipality/ city councils', 'Non-governmental Organizations', 'Parliament', 'Political Party/Politician', 'Private Companies/organizations', 'Public Awareness', 'Reformists', 'State Companies/organizations', 'Supreme Leader', 'University Officials', 'Other', 'None', 'Unknown'
- **Organizer_type**: 'Armed/Separatist group', 'Campaign', 'Formal religious group', 'Formal student group', 'GONGO', 'Informal Group', 'Labour Union', 'NGO/Community', 'Online Community', 'Ordinary Citizens', 'Political Org. Outside Iran', 'Political Org./Party', 'Prayers', 'Syndicate', 'Other', 'Diverse', 'Unknown', 'None'
- **CivilSocietySector**: 'Animal rights', 'Charity', 'Children's rights', 'Cultural', 'Disability rights', 'Economic/trade/business', 'Environmental', 'Ethnic', 'Farmers', 'Human rights', 'Journalists', 'Labour', 'Lawyers', 'Nurses', 'Political', 'Religious', 'Retireds', 'Social', 'Student Movement', 'Teachers', 'Urban', 'Women', 'None', 'Other', 'Diverse', 'Unknown'
- **MainPoliticalSector**: 'Reformist', 'Progovernment', 'Conservative', 'Neutral', 'Other', 'Unknown'

### Event Arena (where did it take place)
- **Arena_type**: 'In front of private companies', 'In front of state buildings', 'International office/ embassy', 'Municipality/ city councils', 'Online', 'Out of residential areas/ Roads', 'Parliament area', 'Prisons', 'Public place', 'Religious places', 'Streets', 'University campuses', 'Working places', 'Other', 'NA', 'Unknown'

## OUTPUT FORMAT
Return ONLY valid JSON with these keys:

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

IMPORTANT: 
- Location names should be in Persian as written in the article
- If information is not available, use "Unknown" or "N/A"
- Be thorough - extract EVERY piece of information you can find
"""