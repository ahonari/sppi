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

## SPECIAL RULES FOR ACCURATE CODING

### 1. Location Rule
The event location is where the protest HAPPENED. If workers from Kermanshah protest in Tehran:
- event_location_name = تهران
- issue_location_name = کرمانشاه

### 2. Form Distinction
- **"public assembly" (تجمع / اجتماع)** = people gathering to show presence, may chant slogans or hold signs, purpose is visibility and numbers
- **"Contacting politicians..." (تماس با سیاستمداران)** = communication-focused action (press conferences, meetings with representatives, sending letters)

### 3. Violence Distinction
- **"Violent protests"** = crowd violence, rioting, fights between protestors and police
- **"Armed conflict"** = organized armed groups, pre-planned attacks by terrorists/military

### 4. Size Estimation
Use the article's description to estimate:
- "تعدادی" (several) → "small group < 15" or "medium group <50"
- "جمعی" (a group) → "medium group <50" or "Large Group <200"
- Specific numbers → use the appropriate category
- If not mentioned → use "unknown"

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

**Petitioning (طومار/درخواست):**
- 'Civil campaigning' (کمپین مدنی یا پویشگری)
- 'Collective open letter' (نامه جمعی اعتراضی)
- 'Contacting politicians, officials, parliament members, media etc.' (تماس با سیاستمداران و مسئولان و رسانه‌ها)
- 'Petitionning' (طومار نویسی)

**Demonstrative protests (legal and nonviolent) (تجمعات قانونی و غیرخشونت‌آمیز):**
- 'demonstration (legal and non-violent)' (تظاهرات)
- 'march/ rally' (راهپیمایی)
- 'public assembly' (تجمع / اجتماع)
- 'electoral assembly' (تجمع انتخاباتی)
- 'vigil' (تحصن)
- 'symbolic demonstrations' (اعتراضات نمادین)

**Confrontational protests (illegal and non violent) (اعتراضات تقابلی غیرقانونی و غیرخشونت‌آمیز):**
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

**Violent protests (اعتراضات خشونت‌آمیز):**
- 'violent demonstration' (تظاهرات خشونت آمیز)
- 'rioting' (شورش خیابانی)
- 'arson and other severe destruction' (آتش زدن)
- 'physical violence against people' (حمله به افراد)

**Armed conflict (درگیری مسلحانه):**
- 'threats' (تهدید)
- 'armed attack' (حمله/درگیری مسلحانه)
- 'bombing' (بمب‌گذاری)
- 'Other' (سایر)

### Mapping: Protest Form → ProtestsCategories
Based on the form you choose, the category will be:

| Protest Form | ProtestsCategories |
|--------------|-------------------|
| Civil campaigning | Petitioning |
| Collective open letter | Petitioning |
| Contacting politicians, officials, parliament members, media etc. | Petitioning |
| Petitionning | Petitioning |
| demonstration (legal and non-violent) | Demonstrative protests (legal and nonviolent) |
| march/ rally | Demonstrative protests (legal and nonviolent) |
| public assembly | Demonstrative protests (legal and nonviolent) |
| electoral assembly | Demonstrative protests (legal and nonviolent) |
| vigil | Demonstrative protests (legal and nonviolent) |
| symbolic demonstrations | Demonstrative protests (legal and nonviolent) |
| blockade | Confrontational protests (illegal and non violent) |
| boycott | Confrontational protests (illegal and non violent) |
| disturbance of meetings | Confrontational protests (illegal and non violent) |
| Hacking | Confrontational protests (illegal and non violent) |
| illegal demonstration (if non-violent) | Confrontational protests (illegal and non violent) |
| limited destruction of property | Confrontational protests (illegal and non violent) |
| occupation | Confrontational protests (illegal and non violent) |
| picket | Confrontational protests (illegal and non violent) |
| sabotage | Confrontational protests (illegal and non violent) |
| self-mutilation (e.g., hunger strike, suicide) | Confrontational protests (illegal and non violent) |
| strike | Confrontational protests (illegal and non violent) |
| symbolic violence | Confrontational protests (illegal and non violent) |
| violent demonstration | Violent protests |
| rioting | Violent protests |
| arson and other severe destruction | Violent protests |
| physical violence against people | Violent protests |
| threats | Armed conflict |
| armed attack | Armed conflict |
| bombing | Armed conflict |
| Other | Armed conflict |

### Issue Categories (Choose ONE that BEST fits)
Choose ONE: 'Business', 'Children', 'Cultural', 'Disability', 'Economic', 'Environmental', 'Ethnic', 'Financial/banking', 'Human rights', 'International', 'Labour', 'Political', 'Religious', 'Social', 'Student/university', 'Urban', 'Women', 'Other', 'Unknown'

### Issue-Specific (Only if applicable - otherwise use 'N/A')
- Environmental: 'Env_Air pollution', 'Env_Decrease biodiversity', 'Env_Deforestation', 'Env_Desertification', 'Env_Drought/ water scarcity', 'Env_Haze', 'Env_Industrial effluents', 'Env_Industrial pollution', 'Env_Soil Degradation', 'Env_Vehicle emissions', 'Env_Waste Disposal'
- International: 'Intl_Islamic', 'Int_Nuclear Technology', 'Intl_Palestine-Israel', 'Intl_Politics', 'Intl_Regional'
- Social: 'Soc_Addiction'
- Urban: 'Urb_City election', 'Urb_Cultural heritage', 'Urb_Drinking water pollution/scarcity', 'Urb_Green spaces', 'Urb_Homeless people', 'Urb_Informal settlers'
- Women: 'Wo_Hijab', 'Wo_Political participation'
- For others: 'N/A'

### Location
- **Local/National/International**: 'Local', 'National', 'International'
- **Location_Category**: 'Capital', 'Province Center', 'City', 'Town', 'Rural', 'National', 'NA'

### Size of Participants - Clear Categories
Use these specific thresholds:
- "1 person" - Solo protest
- "small group < 15" - Fewer than 15 people
- "medium group < 50" - 15 to 50 people
- "Large Group < 200" - 50 to 200 people
- "Mob < 1000" - 200 to 1000 people
- "thousands, +1000" - 1000 to 10,000 people
- "massive > 100,000" - Over 100,000 people
- "unknown" - Not mentioned or cannot estimate

If the article says "تعدادی" (several) → use "small group < 15" or "medium group <50"
If the article says "جمعی" (a group) → use "medium group <50" or "Large Group <200"
If the article gives a specific number, use the appropriate category

### Actors
- **target** (who is the protest directed against): 'Conservatives', 'Government', 'International Institution/Country', 'Judiciary', 'Law Enforcement Force', 'Local authorities/agencies', 'Military base', 'Ministries', 'Municipality/ city councils', 'Non-governmental Organizations', 'Parliament', 'Political Party/Politician', 'Private Companies/organizations', 'Public Awareness', 'Reformists', 'State Companies/organizations', 'Supreme Leader', 'University Officials', 'Other', 'None', 'Unknown'
- **Organizer_type**: 'Armed/Separatist group', 'Campaign', 'Formal religious group', 'Formal student group', 'GONGO', 'Informal Group', 'Labour Union', 'NGO/Community', 'Online Community', 'Ordinary Citizens', 'Political Org. Outside Iran', 'Political Org./Party', 'Prayers', 'Syndicate', 'Other', 'Diverse', 'Unknown', 'None'
- **CivilSocietySector**: 'Animal rights', 'Charity', 'Children's rights', 'Cultural', 'Disability rights', 'Economic/trade/business', 'Environmental', 'Ethnic', 'Farmers', 'Human rights', 'Journalists', 'Labour', 'Lawyers', 'Nurses', 'Political', 'Religious', 'Retireds', 'Social', 'Student Movement', 'Teachers', 'Urban', 'Women', 'None', 'Other', 'Diverse', 'Unknown'
- **MainPoliticalSector**: 'Reformist', 'Progovernment', 'Conservative', 'Neutral', 'Other', 'Unknown'

### Event Arena
- **arena_name**: Specific location in Persian (e.g., "مقابل مجلس شورای اسلامی", "خیابان طالقانی", "دانشگاه تهران")
- **arena_type**: 'In front of private companies', 'In front of state buildings', 'International office/ embassy', 'Municipality/ city councils', 'Online', 'Out of residential areas/ Roads', 'Parliament area', 'Prisons', 'Public place', 'Religious places', 'Streets', 'University campuses', 'Working places', 'Other', 'NA', 'Unknown'

### Location Coding Rules
**IMPORTANT: Separate "Issue Location" from "Event Location"**

- **event_location_name**: Where the protest ACTUALLY took place (physical location of the gathering)
- **issue_location_name**: Where the problem is happening (may be different from event location)

Example: Workers from Kermanshah protest in Tehran → event_location = تهران, issue_location = کرمانشاه
Example: Teachers protest in their own city → event_location = [city name], issue_location = [same city]

If the article says "in front of Parliament" → event_location is تهران (or the city where Parliament is located)

## OUTPUT FORMAT
Return ONLY valid JSON with these keys:

{{
  "relevance": "Yes",
  "duplicate": "No",
  "protests_categories": "",
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
  "arena_name": "",
  "arena_type": "",
  "event_date": "",
  "is_multi_day": "No",
  "date_range_start": "",
  "date_range_end": "",
  "days_duration": 1
}}

IMPORTANT: 
- Location names should be in Persian as written in the article
- arena_name should be the specific location in Persian (e.g., "مقابل مجلس شورای اسلامی")
- If information is not available, use "Unknown" or "N/A"
- Be thorough - extract EVERY piece of information you can find
"""