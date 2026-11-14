from .store import INDICATORS

REGIONS = {
    "general_health": ("General Health", "Daily health checks, fatigue, and temperature concerns.", ["Fatigue", "General discomfort", "Temperature concern", "Daily health check"], "fatigue sleep general wellness"),
    "head_brain": ("Head & Brain", "Explore sleep, headaches, and changes in concentration.", ["Headache", "Sleep concern", "Concentration concern"], "sleep brain concentration"),
    "chest_heart": ("Cardiovascular", "Review heart rate, palpitations, chest discomfort, and blood pressure.", ["Palpitations", "Heart-rate concern", "Blood-pressure concern", "Chest discomfort"], "cardiovascular heart blood pressure"),
    "abdomen": ("Abdomen", "Explore NASA research about nutrition and the spaceflight environment.", [], "abdomen nutrition environment"),
    "musculoskeletal": ("Musculoskeletal", "Explore NASA research on bone and muscle changes in microgravity.", [], "bone muscle musculoskeletal gravity"),
}
AHA = "https://www.heart.org/en/about-us/heart-attack-and-stroke-symptoms"
NASA_MED = "https://www.nasa.gov/ochmo/health-and-medical-systems/in-flight-medical-care/"
GUIDANCE = {
    "emergency": {
        "title": "Alert the designated crew medical responder now",
        "steps": ["Use your mission’s approved emergency response procedures.", "Contact ground medical support through the mission’s emergency communication pathway as directed."],
        "sources": [NASA_MED, AHA, "https://www.cdc.gov/stroke/signs-symptoms/"], "review_status": "source_checked_prototype", "procedure_available": False,
    },
    "crew_review": {
        "title": "Share this assessment with your crew medical contact",
        "steps": ["Share the recorded concern, its onset, and any readings you collected.", "Use your mission’s medical reporting procedure for follow-up."],
        "sources": [NASA_MED], "review_status": "source_checked_prototype", "procedure_available": False,
    },
    "routine": {
        "title": "Continue your scheduled mission health checks",
        "steps": ["Keep this entry in your mission log.", "Report new or persistent concerns through your mission’s medical reporting procedure."],
        "sources": [NASA_MED], "review_status": "source_checked_prototype", "procedure_available": False,
    },
}

BP = "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings/monitoring-your-blood-pressure-at-home"
GUIDE_DATA = {
    "resting_hr_bpm": ("Tracks pulse at rest for comparison over time.", "Approved pulse monitor, or timer for a manual wrist pulse.", "After resting, count wrist pulse beats for one full minute. Record the context.", "Avoid comparing a post-exertion pulse with resting readings.", "https://medlineplus.gov/ency/article/003399.htm"),
    "sleep_hours": ("Tracks sleep duration alongside fatigue and alertness.", "Sleep log or approved tracker.", "Record actual estimated sleep during your main sleep period, excluding time spent awake.", "Record the estimate consistently. Leave it blank if unknown.", "https://www.cdc.gov/niosh/work-hour-training-for-nurses/10/sleepdiary.pdf"),
    "systolic_bp_mmhg": ("Tracks the upper pressure reading.", "Approved upper-arm monitor with a correctly sized cuff.", "Use the device and positioning specified in your onboard procedure. Record the upper reading.", "Record the resting context and use the correct cuff size.", BP),
    "diastolic_bp_mmhg": ("Tracks the lower pressure reading.", "Approved upper-arm monitor with a correctly sized cuff.", "Use the device and positioning specified in your onboard procedure. Record the lower reading.", "Use the same measurement context as the systolic reading.", BP),
    "body_temp_c": ("Tracks body temperature over time.", "Approved digital thermometer.", "Use the method specified by the device and mission procedure. Record the reading in Celsius and note the measurement site.", "Use a consistent site and record the unit.", "https://medlineplus.gov/ency/article/003400.htm"),
    "blood_glucose_mgdl": ("Records glucose when scheduled by the crew medical team.", "Mission-approved glucose monitor and supplies.", "Follow the prescribed measurement schedule and device procedure. Record the value and timing relative to meals when applicable.", "Confirm the monitor is displaying mg/dL.", "https://medlineplus.gov/lab-tests/blood-glucose-test/"),
}

def guides():
    return [{"indicator": key, "title": INDICATORS[key][0], "unit": INDICATORS[key][1],
             "why": parts[0], "equipment": parts[1], "instructions": parts[2], "common_mistakes": parts[3],
             "source": parts[4], "limitations": "Reference for the prototype. Follow device-specific and approved mission procedures."}
            for key, parts in GUIDE_DATA.items()]

def region_payload(key):
    title, description, concerns, topic = REGIONS[key]
    return {"id": key, "title": title, "description": description, "concerns": concerns, "evidence_topic": topic}

def choice(key, prompt, options, description=""):
    return {"id": key, "prompt": prompt, "type": "choice", "options": options, "description": description}

def question_list(region, concern, answers):
    warning = "Chest pain or pressure, severe trouble breathing, collapse, or sudden face droop, arm weakness, or speech difficulty."
    if region == "head_brain":
        warning += " Also include a sudden severe headache."
    questions = [choice("urgent", "Are any of these warning signs present now?", ["No", "Yes", "Unsure"], warning)]
    if concern != "Daily health check":
        questions.append(choice("onset", "When did this concern begin?", ["Today", "In the last few days", "More than a week ago", "Unsure"]))
        questions.append(choice("recurring", "Has this concern happened before on this mission?", ["No", "Yes", "Unsure"]))
        if answers.get("recurring") == "Yes":
            questions.append({"id": "notes", "prompt": "What changed since the last episode?", "type": "text",
                              "description": "Add a short note or skip this question.", "optional": True})
    indicators = ["resting_hr_bpm", "sleep_hours"]
    if region == "chest_heart":
        indicators += ["systolic_bp_mmhg", "diastolic_bp_mmhg"]
    if concern in ("Temperature concern", "Daily health check", "General discomfort"):
        indicators += ["body_temp_c"]
    if concern in ("Fatigue", "Headache"):
        indicators += ["fatigue_score_0_10" if concern == "Fatigue" else "headache_score_0_10"]
    for key in indicators:
        name, unit, minimum, maximum = INDICATORS[key]
        questions.append({"id": key, "prompt": f"Record your {name.lower()}", "type": "number", "unit": unit,
                          "minimum": minimum, "maximum": maximum, "optional": True,
                          "guide_id": key if key in GUIDE_DATA else None})
    return questions
