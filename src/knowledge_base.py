from __future__ import annotations

OSHA_RULES = [
    {
        "title": "Fall Protection At Unprotected Edges",
        "hazard_category": "fall",
        "keywords": ["edge", "roof", "leading edge", "open side", "elevated", "fall", "unguarded"],
        "control_hint": "Workers near elevated unprotected edges should have guardrails, covers, travel restraint, or personal fall arrest.",
    },
    {
        "title": "Ladder Setup And Three-Point Contact",
        "hazard_category": "fall",
        "keywords": ["ladder", "extension ladder", "step ladder", "climbing"],
        "control_hint": "Ladders should be stable, properly angled, extend where needed, and be used with controlled access and three-point contact.",
    },
    {
        "title": "Scaffold Access And Guarding",
        "hazard_category": "fall",
        "keywords": ["scaffold", "plank", "platform", "baker scaffold"],
        "control_hint": "Scaffold platforms should have complete decking, safe access, and fall protection where required.",
    },
    {
        "title": "Electrical Exposure And Temporary Power",
        "hazard_category": "electrical",
        "keywords": ["electrical", "cord", "temporary power", "panel", "energized", "exposed wire"],
        "control_hint": "Temporary power should be protected from damage, cords managed, and energized parts guarded from contact.",
    },
    {
        "title": "Struck-By Controls Around Equipment",
        "hazard_category": "struck-by",
        "keywords": ["forklift", "excavator", "loader", "truck", "crane", "swing radius", "backing"],
        "control_hint": "Heavy equipment zones need separation, spotters or controls, and clear worker awareness of movement paths.",
    },
    {
        "title": "Housekeeping And Access Control",
        "hazard_category": "housekeeping",
        "keywords": ["debris", "trip", "blocked", "housekeeping", "material pile", "access path"],
        "control_hint": "Walking surfaces and access paths should stay clear of debris, stored material, and unmanaged cords or hoses.",
    },
    {
        "title": "PPE For Active Work Exposure",
        "hazard_category": "ppe",
        "keywords": ["ppe", "hard hat", "vest", "glasses", "gloves", "harness", "no helmet"],
        "control_hint": "Required PPE should match the active exposure and remain in use in the work area.",
    },
    {
        "title": "Excavation Edge And Access Safety",
        "hazard_category": "excavation",
        "keywords": ["trench", "excavation", "spoils", "shoring", "sloping"],
        "control_hint": "Excavations need access, spoil separation, and protective systems based on depth and conditions.",
    },
]
