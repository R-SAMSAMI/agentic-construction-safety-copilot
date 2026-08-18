from __future__ import annotations

from datetime import date

import streamlit as st
from dotenv import load_dotenv

from src.agent_workflow import ObservationContext, build_demo_agent_run
from src.openai_client import SafetyQuotaError, analyze_site_safety_case
from src.reporting import build_markdown_report

load_dotenv()

PROJECT_CASES = {
    "Building - Concrete": {
        "default_case": "Concrete Deck Pour",
        "cases": {
            "Concrete Deck Pour": {
                "project_name": "Riverfront Tower Podium",
                "contractor_name": "Atlas Concrete",
                "work_area": "Level 4 east deck pour",
                "work_type": "Concrete",
                "shift": "Day",
                "weather": "Windy",
                "crew_size": 8,
                "observation_notes": (
                    "Concrete crew placing and finishing slab at the east deck pour. Workers are moving between pump line access, "
                    "rebar mats, and material staging areas. Housekeeping is uneven near the ladder landing, one access point is tight, "
                    "and edge protection should be confirmed before the next pour sequence continues."
                ),
            },
            "Formwork And Rebar Access": {
                "project_name": "Riverside Medical Tower",
                "contractor_name": "Atlas Concrete",
                "work_area": "North deck rebar and formwork edge",
                "work_type": "Concrete",
                "shift": "Day",
                "weather": "Clear",
                "crew_size": 6,
                "observation_notes": (
                    "Crew tying rebar and adjusting edge formwork before the next concrete placement. Material bundles and hoses are reducing clear access, "
                    "one ladder approach is partially obstructed, and workers are crossing between active placement zones and stored material."
                ),
            },
            "Concrete Pump And Equipment Interface": {
                "project_name": "Union Square Mixed-Use Podium",
                "contractor_name": "Summit Site Works",
                "work_area": "South deck pump staging area",
                "work_type": "Site logistics",
                "shift": "Day",
                "weather": "Mixed conditions",
                "crew_size": 7,
                "observation_notes": (
                    "Concrete pump activity, truck movement, and crew access are overlapping in the active pour zone. Spotter coverage should be confirmed, "
                    "pedestrian routing is tight near staging, and the work area needs clearer separation between moving equipment and the finishing crew."
                ),
            },
        },
    },
    "Building - Steel": {
        "default_case": "Open Edge Decking",
        "cases": {
            "Open Edge Decking": {
                "project_name": "Harbor Office Tower",
                "contractor_name": "Northshore Steel",
                "work_area": "Level 12 east bay",
                "work_type": "Steel erection",
                "shift": "Day",
                "weather": "Windy",
                "crew_size": 5,
                "observation_notes": (
                    "Decking crew working near an open edge while landing material bundles. One worker is transitioning across incomplete decking, "
                    "control lines should be confirmed, and the active edge needs a clear review before the next material pick."
                ),
            },
            "Column Connection And Material Landing": {
                "project_name": "Metro Center Expansion",
                "contractor_name": "Northshore Steel",
                "work_area": "Level 9 column line C",
                "work_type": "Steel erection",
                "shift": "Day",
                "weather": "Clear",
                "crew_size": 4,
                "observation_notes": (
                    "Ironworkers are aligning a beam connection while a second crew prepares the next material landing area. Access routes are narrow, "
                    "stored decking bundles reduce maneuvering space, and swing-radius awareness needs to be reinforced."
                ),
            },
            "Metal Deck Access Housekeeping": {
                "project_name": "State Street Office Core",
                "contractor_name": "Beacon Structural",
                "work_area": "Level 7 temporary access path",
                "work_type": "Steel erection",
                "shift": "Day",
                "weather": "Wet",
                "crew_size": 6,
                "observation_notes": (
                    "Temporary access across metal deck is being used during framing follow-up work. Wet conditions, cut material, and stored tools are reducing clear access, "
                    "and the route should be reviewed before additional personnel use the area."
                ),
            },
        },
    },
    "Civil / Bridge": {
        "default_case": "Bridge Deck Pour",
        "cases": {
            "Bridge Deck Pour": {
                "project_name": "I-95 Deck Rehabilitation",
                "contractor_name": "Summit Site Works",
                "work_area": "Southbound bridge pour zone",
                "work_type": "Concrete",
                "shift": "Day",
                "weather": "Mixed conditions",
                "crew_size": 7,
                "observation_notes": (
                    "Bridge deck crew placing concrete while pump hoses, screed access, and parapet-side movement overlap in the active work zone. "
                    "Housekeeping and edge access should be reviewed before the next section is placed."
                ),
            },
            "Barrier And Parapet Access": {
                "project_name": "Harbor Transit Expansion",
                "contractor_name": "Atlas Civil Group",
                "work_area": "Span 3 parapet work zone",
                "work_type": "Concrete",
                "shift": "Day",
                "weather": "Windy",
                "crew_size": 5,
                "observation_notes": (
                    "Crew installing barrier and parapet reinforcement near the edge of the bridge deck. Material staging is tight, access along the work face is narrow, "
                    "and crew movement should be reviewed before the next sequence begins."
                ),
            },
            "Excavation And Equipment Separation": {
                "project_name": "River Crossing Utility Relocation",
                "contractor_name": "Atlas Civil Group",
                "work_area": "Approach excavation north side",
                "work_type": "Excavation",
                "shift": "Day",
                "weather": "Wet",
                "crew_size": 6,
                "observation_notes": (
                    "Excavation crew and equipment operators are working in close proximity near the north approach. Spoil placement, pedestrian access, and equipment routing "
                    "need clearer separation before the work area expands."
                ),
            },
        },
    },
    "Roofing / Envelope": {
        "default_case": "Roof Edge Material Handling",
        "cases": {
            "Roof Edge Material Handling": {
                "project_name": "Civic Center Envelope Upgrade",
                "contractor_name": "Skyline Roofing",
                "work_area": "South roof edge",
                "work_type": "Roofing",
                "shift": "Day",
                "weather": "Windy",
                "crew_size": 5,
                "observation_notes": (
                    "Roofing crew staging materials near the south edge while membrane work continues. Access lanes are tightening around stored materials, "
                    "and edge controls should be verified before the next material move."
                ),
            },
            "Facade Swing Stage Staging": {
                "project_name": "Broad Street Facade Renewal",
                "contractor_name": "Elevate Facades",
                "work_area": "North elevation swing-stage setup",
                "work_type": "General trades",
                "shift": "Day",
                "weather": "Clear",
                "crew_size": 4,
                "observation_notes": (
                    "Facade crew is staging swing-stage gear and materials at the roof line. Stored components are reducing clear setup space, "
                    "and the roof staging arrangement should be reviewed before suspended access begins."
                ),
            },
            "Roof Drain And Access Housekeeping": {
                "project_name": "University Hall Roof Replacement",
                "contractor_name": "Skyline Roofing",
                "work_area": "West roof drain path",
                "work_type": "Roofing",
                "shift": "Day",
                "weather": "Wet",
                "crew_size": 6,
                "observation_notes": (
                    "Crew is working around roof drains and access routes after overnight rain. Wet surfaces, hoses, and material wrappers are affecting housekeeping, "
                    "and the route should be corrected before more workers move through the area."
                ),
            },
        },
    },
    "MEP / Interiors": {
        "default_case": "Temporary Power And Access",
        "cases": {
            "Temporary Power And Access": {
                "project_name": "Central Lab Fit-Out",
                "contractor_name": "Beacon Electrical",
                "work_area": "Level 2 corridor rough-in zone",
                "work_type": "MEP",
                "shift": "Night",
                "weather": "Indoor",
                "crew_size": 5,
                "observation_notes": (
                    "Electrical rough-in is active in the corridor while temporary power, rolling carts, and material staging are narrowing access. "
                    "Cord management and work-area separation should be reviewed before the shift continues."
                ),
            },
            "Overhead Mechanical Access": {
                "project_name": "Riverside Medical Tower",
                "contractor_name": "Summit Mechanical",
                "work_area": "Level 6 mechanical room entry",
                "work_type": "MEP",
                "shift": "Day",
                "weather": "Indoor",
                "crew_size": 4,
                "observation_notes": (
                    "Mechanical crew is using ladders and rolling access equipment to tie in overhead ductwork. Stored material and active trades are creating a tight work face, "
                    "and access controls should be reviewed before additional overhead work proceeds."
                ),
            },
            "Interior Housekeeping And Multi-Trade Overlap": {
                "project_name": "Innovation Center Renovation",
                "contractor_name": "Beacon Electrical",
                "work_area": "Level 3 corridor and room entries",
                "work_type": "MEP",
                "shift": "Day",
                "weather": "Indoor",
                "crew_size": 7,
                "observation_notes": (
                    "Electrical and finishes crews are sharing corridor access while carts, boxes, and temporary power leads reduce clear egress. "
                    "The area needs housekeeping attention and clearer work-zone separation before production ramps up."
                ),
            },
        },
    },
}

DEFAULT_PROJECT_TYPE = "Building - Concrete"


def initialize_state() -> None:
    defaults = PROJECT_CASES[DEFAULT_PROJECT_TYPE]["cases"][PROJECT_CASES[DEFAULT_PROJECT_TYPE]["default_case"]]
    st.session_state.setdefault("selected_project_type", DEFAULT_PROJECT_TYPE)
    st.session_state.setdefault("selected_case", PROJECT_CASES[DEFAULT_PROJECT_TYPE]["default_case"])
    st.session_state.setdefault("project_name", defaults["project_name"])
    st.session_state.setdefault("contractor_name", defaults["contractor_name"])
    st.session_state.setdefault("work_area", defaults["work_area"])
    st.session_state.setdefault("work_type", defaults["work_type"])
    st.session_state.setdefault("shift", defaults["shift"])
    st.session_state.setdefault("weather", defaults["weather"])
    st.session_state.setdefault("crew_size", defaults["crew_size"])
    st.session_state.setdefault("observation_notes", defaults["observation_notes"])
    st.session_state.setdefault("latest_result", None)
    st.session_state.setdefault("latest_context", None)
    st.session_state.setdefault("latest_observation_date", date.today())


def apply_case(project_type: str, case_name: str) -> None:
    scenario = PROJECT_CASES[project_type]["cases"][case_name]
    st.session_state["selected_project_type"] = project_type
    st.session_state["selected_case"] = case_name
    st.session_state["project_name"] = scenario["project_name"]
    st.session_state["contractor_name"] = scenario["contractor_name"]
    st.session_state["work_area"] = scenario["work_area"]
    st.session_state["work_type"] = scenario["work_type"]
    st.session_state["shift"] = scenario["shift"]
    st.session_state["weather"] = scenario["weather"]
    st.session_state["crew_size"] = scenario["crew_size"]
    st.session_state["observation_notes"] = scenario["observation_notes"]


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

        :root {
            --bg: #f5efe3;
            --ink: #1f2a22;
            --muted: #5c665f;
            --accent: #c65a28;
            --accent-dark: #8f3d17;
            --cream: #fff8f2;
            --olive: #6f7c45;
            --line: rgba(198, 90, 40, 0.10);
            --panel: rgba(255, 249, 238, 0.88);
            --panel-strong: rgba(255, 252, 246, 0.96);
            --shadow: 0 18px 40px rgba(75, 56, 38, 0.10);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(198, 90, 40, 0.18), transparent 26%),
                radial-gradient(circle at top right, rgba(143, 61, 23, 0.10), transparent 20%),
                linear-gradient(180deg, #f9f3e8 0%, #f5efe3 52%, #efe5d7 100%);
            color: var(--ink);
            font-family: 'IBM Plex Sans', sans-serif;
        }

        .block-container {
            max-width: 1220px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3 {
            font-family: 'Space Grotesk', sans-serif !important;
            color: var(--ink);
            letter-spacing: -0.03em;
        }

        [data-testid="stSidebar"] {
            background: rgba(255, 249, 238, 0.92);
            border-right: 1px solid var(--line);
        }

        .hero {
            padding: 1.65rem 1.8rem;
            border-radius: 28px;
            background: linear-gradient(135deg, rgba(198, 90, 40, 0.98) 0%, rgba(143, 61, 23, 0.98) 100%);
            color: var(--cream);
            box-shadow: 0 20px 45px rgba(143, 61, 23, 0.18);
            margin-bottom: 1.25rem;
        }

        .hero h1 {
            margin: 0;
            font-size: 2.9rem;
            font-weight: 700;
        }

        .hero p {
            margin: 0.75rem 0 0;
            max-width: 820px;
            font-size: 1rem;
            line-height: 1.6;
            color: rgba(255, 248, 242, 0.92);
        }

        .hero-note {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.38rem 0.78rem;
            border-radius: 999px;
            background: rgba(255, 248, 242, 0.16);
            color: var(--cream);
            font-size: 0.84rem;
            font-weight: 600;
        }

        .panel {
            background: var(--panel-strong);
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1rem 1.05rem;
            box-shadow: var(--shadow);
        }

        .panel-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--accent-dark);
            margin-bottom: 0.12rem;
        }

        .panel-copy {
            color: var(--muted);
            font-size: 0.92rem;
            margin-bottom: 0.8rem;
        }

        .metric-shell {
            border-radius: 20px;
            padding: 0.15rem;
            background: linear-gradient(135deg, rgba(198, 90, 40, 0.18), rgba(143, 61, 23, 0.12));
        }

        .metric-core {
            background: rgba(255, 252, 246, 0.95);
            border-radius: 18px;
            padding: 0.85rem 1rem;
            min-height: 116px;
        }

        .metric-label {
            color: #7b6a5c;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.5rem;
        }

        .metric-value {
            color: var(--ink);
            font-size: 2rem;
            font-weight: 700;
            line-height: 1;
            margin-bottom: 0.45rem;
        }

        .metric-detail {
            color: var(--muted);
            font-size: 0.9rem;
            line-height: 1.45;
        }

        .summary-list {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.75rem 1.2rem;
        }

        .summary-item-label {
            color: var(--muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.15rem;
        }

        .summary-item-value {
            color: var(--ink);
            font-size: 1rem;
            font-weight: 600;
        }

        .card {
            background: rgba(255, 252, 246, 0.96);
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem;
            box-shadow: 0 14px 30px rgba(143, 61, 23, 0.07);
            margin-bottom: 0.85rem;
        }

        .card h4 {
            margin: 0 0 0.35rem 0;
            color: var(--ink);
            font-size: 1.05rem;
        }

        .card-meta {
            color: var(--muted);
            font-size: 0.9rem;
            margin-bottom: 0.45rem;
        }

        .status-tag {
            display: inline-block;
            border-radius: 999px;
            padding: 0.22rem 0.62rem;
            font-size: 0.78rem;
            font-weight: 700;
            margin-right: 0.35rem;
            margin-bottom: 0.35rem;
        }

        .tag-alert {
            background: rgba(198, 90, 40, 0.12);
            color: var(--accent-dark);
            border: 1px solid rgba(198, 90, 40, 0.20);
        }

        .tag-ok {
            background: rgba(111, 124, 69, 0.12);
            color: #556136;
            border: 1px solid rgba(111, 124, 69, 0.22);
        }

        .tag-review {
            background: rgba(227, 177, 70, 0.16);
            color: #8a6220;
            border: 1px solid rgba(227, 177, 70, 0.24);
        }

        div[data-testid="stFileUploader"],
        div[data-testid="stTextInput"],
        div[data-testid="stTextArea"],
        div[data-testid="stDateInput"],
        div[data-testid="stNumberInput"],
        div[data-testid="stSelectbox"] {
            background: rgba(255,255,255,0.45);
            border-radius: 18px;
            padding: 0.3rem 0.5rem 0.5rem 0.5rem;
            border: 1px solid rgba(31, 42, 34, 0.05);
        }

        .stButton > button, .stDownloadButton > button {
            background: linear-gradient(135deg, var(--accent), #d77538) !important;
            color: white !important;
            border: none !important;
            border-radius: 16px !important;
            padding: 0.75rem 1rem !important;
            font-weight: 700 !important;
            box-shadow: 0 10px 24px rgba(198, 90, 40, 0.22);
        }

        button[data-baseweb="tab"] {
            background: rgba(255, 252, 246, 0.74);
            border-radius: 999px;
            padding: 0.5rem 1rem;
        }

        button[data-baseweb="tab"][aria-selected="true"] {
            background: rgba(143, 61, 23, 0.96);
            color: var(--cream);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric(title: str, value: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="metric-shell">
            <div class="metric-core">
                <div class="metric-label">{title}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-detail">{detail}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_intro(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="panel-title">{title}</div>
        <div class="panel-copy">{copy}</div>
        """,
        unsafe_allow_html=True,
    )


def status_class(status: str) -> str:
    if status == "likely compliant":
        return "tag-ok"
    if status == "likely non-compliant":
        return "tag-alert"
    return "tag-review"


initialize_state()
inject_styles()

with st.sidebar:
    st.header("Review Controls")
    st.caption("Choose a project type, load a realistic field case, confirm the review mode, and then run the safety review.")
    selected_project_type = st.selectbox(
        "Project type",
        options=list(PROJECT_CASES.keys()),
        index=list(PROJECT_CASES.keys()).index(st.session_state["selected_project_type"]),
    )
    available_cases = list(PROJECT_CASES[selected_project_type]["cases"].keys())
    current_case = st.session_state["selected_case"]
    if current_case not in available_cases:
        current_case = PROJECT_CASES[selected_project_type]["default_case"]
    selected_case = st.selectbox(
        "Review case",
        options=available_cases,
        index=available_cases.index(current_case),
    )
    if (
        selected_project_type != st.session_state["selected_project_type"]
        or selected_case != st.session_state["selected_case"]
    ):
        apply_case(selected_project_type, selected_case)
        st.rerun()

    demo_mode = st.toggle("Sample review mode", value=True)
    if demo_mode:
        st.success("Sample review mode is on. Use this for consistent walkthroughs and portfolio screenshots.")
    else:
        st.warning("Live review mode is on. This uses your OpenAI API credits for richer interpretation.")

    st.markdown("---")
    st.markdown("**Review focus**")
    if selected_project_type == "Building - Concrete":
        st.write("- Concrete placement and finishing")
        st.write("- Rebar, formwork, and access")
        st.write("- Pump staging and edge conditions")
        st.write("- Housekeeping at active deck pours")
    elif selected_project_type == "Building - Steel":
        st.write("- Decking and open-edge exposure")
        st.write("- Material landing and swing radius")
        st.write("- Temporary access across steel framing")
        st.write("- Stored material and route control")
    elif selected_project_type == "Civil / Bridge":
        st.write("- Bridge deck, parapet, and edge access")
        st.write("- Excavation and equipment separation")
        st.write("- Civil staging and spoil management")
        st.write("- Concrete placement in active roadway zones")
    elif selected_project_type == "Roofing / Envelope":
        st.write("- Roof-edge staging and material handling")
        st.write("- Wet surfaces and drain-path access")
        st.write("- Suspended access setup")
        st.write("- Envelope work area housekeeping")
    else:
        st.write("- Temporary power and access control")
        st.write("- Overhead work and ladder positioning")
        st.write("- Interior egress and multi-trade overlap")
        st.write("- Housekeeping in active fit-out areas")
    st.markdown("---")
    st.info(
        "Decision support only. Field leadership, competent person review, OSHA interpretation, and stop-work authority remain human responsibilities."
    )


st.markdown(
    """
    <div class="hero">
        <h1>Agentic Construction Safety Copilot</h1>
        <p>
            Field safety review workspace for converting active site observations into structured signals,
            risk assessment, control review findings, and prioritized corrective actions for construction teams.
        </p>
        <div class="hero-note">Construction safety review workflow with risk, compliance, and action planning</div>
    </div>
    """,
    unsafe_allow_html=True,
)

top_left, top_right = st.columns((1.12, 0.88), gap="large")

with top_left:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    section_intro("Observation Intake", "Capture the work area, crew conditions, and field note you want reviewed.")
    st.text_input("Project name", key="project_name", placeholder="Riverfront Tower Podium")
    st.text_input("Contractor", key="contractor_name", placeholder="Atlas Concrete")
    st.text_input("Work area", key="work_area", placeholder="Level 4 east deck pour")
    row_a, row_b = st.columns(2)
    with row_a:
        st.selectbox(
            "Work type",
            ["Steel erection", "Concrete", "Roofing", "MEP", "Site logistics", "Excavation", "General trades"],
            key="work_type",
        )
    with row_b:
        st.selectbox("Shift", ["Day", "Night"], key="shift")
    row_c, row_d = st.columns(2)
    with row_c:
        st.selectbox(
            "Weather / conditions",
            ["Clear", "Windy", "Wet", "Cold", "Hot", "Indoor", "Mixed conditions"],
            key="weather",
        )
    with row_d:
        st.number_input("Crew size", min_value=1, max_value=50, step=1, key="crew_size")
    observation_date = st.date_input("Observation date", value=st.session_state["latest_observation_date"])
    uploaded_files = st.file_uploader(
        "Supporting photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True,
        help="Optional field photos for added context in live review mode.",
    )
    st.text_area(
        "Observation note",
        key="observation_notes",
        height=170,
        placeholder="Describe what the crew is doing, where the work is happening, and any conditions that need review.",
    )
    run_button = st.button("Run Safety Review", type="primary", width="stretch")
    st.markdown("</div>", unsafe_allow_html=True)

with top_right:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    section_intro("Case Summary", "High-level orientation for the active observation before the review is run.")
    st.markdown(
        f"""
        <div class="summary-list">
            <div>
                <div class="summary-item-label">Project Type</div>
                <div class="summary-item-value">{st.session_state['selected_project_type']}</div>
            </div>
            <div>
                <div class="summary-item-label">Review Case</div>
                <div class="summary-item-value">{st.session_state['selected_case']}</div>
            </div>
            <div>
                <div class="summary-item-label">Project</div>
                <div class="summary-item-value">{st.session_state['project_name'] or 'Not entered'}</div>
            </div>
            <div>
                <div class="summary-item-label">Contractor</div>
                <div class="summary-item-value">{st.session_state['contractor_name'] or 'Not entered'}</div>
            </div>
            <div>
                <div class="summary-item-label">Work Area</div>
                <div class="summary-item-value">{st.session_state['work_area'] or 'Not entered'}</div>
            </div>
            <div>
                <div class="summary-item-label">Work Type</div>
                <div class="summary-item-value">{st.session_state['work_type']}</div>
            </div>
            <div>
                <div class="summary-item-label">Shift</div>
                <div class="summary-item-value">{st.session_state['shift']}</div>
            </div>
            <div>
                <div class="summary-item-label">Weather</div>
                <div class="summary-item-value">{st.session_state['weather']}</div>
            </div>
            <div>
                <div class="summary-item-label">Crew Size</div>
                <div class="summary-item-value">{st.session_state['crew_size']}</div>
            </div>
            <div>
                <div class="summary-item-label">Photos Attached</div>
                <div class="summary-item-value">{len(uploaded_files) if uploaded_files else 0}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div style="height:0.9rem;"></div>', unsafe_allow_html=True)
    st.markdown("**Latest observation note**")
    if st.session_state["observation_notes"].strip():
        st.write(st.session_state["observation_notes"])
    else:
        st.caption("No observation note has been entered yet.")
    st.markdown("</div>", unsafe_allow_html=True)


if run_button:
    context = ObservationContext(
        project_name=st.session_state["project_name"].strip(),
        contractor_name=st.session_state["contractor_name"].strip(),
        work_area=st.session_state["work_area"].strip(),
        work_type=st.session_state["work_type"],
        shift=st.session_state["shift"],
        weather=st.session_state["weather"],
        crew_size=int(st.session_state["crew_size"]),
        notes=st.session_state["observation_notes"].strip(),
        filenames=[uploaded.name for uploaded in uploaded_files] if uploaded_files else [],
    )
    image_payloads = [
        {"name": uploaded.name, "bytes": uploaded.getvalue(), "mime_type": uploaded.type or "image/jpeg"}
        for uploaded in uploaded_files or []
    ]

    with st.spinner("Running safety review..."):
        try:
            if demo_mode:
                result = build_demo_agent_run(context)
            else:
                result = analyze_site_safety_case(context=context, image_payloads=image_payloads)
        except SafetyQuotaError as exc:
            st.error(str(exc))
            st.info("Switch back to Sample review mode in the sidebar if you want a consistent review without API usage.")
        except Exception as exc:
            st.error(str(exc))
        else:
            st.session_state["latest_result"] = result
            st.session_state["latest_context"] = context
            st.session_state["latest_observation_date"] = observation_date
            st.success("Safety review complete.")


result = st.session_state.get("latest_result")
saved_context = st.session_state.get("latest_context")
saved_date = st.session_state.get("latest_observation_date")

if result and saved_context:
    report_markdown = build_markdown_report(result, context=saved_context, observation_date=saved_date)
    likely_non_compliant = sum(item.status == "likely non-compliant" for item in result.compliance_findings)

    metric_columns = st.columns(4)
    metrics = [
        ("Primary Risk", result.reasoning.primary_risk_level.title(), "Overall field posture for the reviewed case."),
        ("Signals", str(len(result.observation_signals)), "Structured field cues extracted from the note and evidence."),
        ("Control Flags", str(likely_non_compliant), "Items that appear to need immediate correction or escalation."),
        ("Action Items", str(len(result.action_plan)), "Corrective actions prepared for field leadership."),
    ]
    for column, (title, value, detail) in zip(metric_columns, metrics):
        with column:
            render_metric(title, value, detail)

    overview_tab, controls_tab, briefing_tab = st.tabs(["Overview", "Control Review", "Field Briefing"])

    with overview_tab:
        left, right = st.columns((1.08, 0.92), gap="large")
        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            section_intro("Executive Brief", "Supervisor-ready summary of the observation and the resulting safety posture.")
            st.write(result.executive_brief)
            st.markdown("**Risk assessment**")
            st.write(result.reasoning.risk_summary)
            st.markdown("**Compounding factors**")
            for factor in result.reasoning.compounding_factors:
                st.write(f"- {factor}")
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            section_intro("Field Signals", "Structured signals extracted from the active observation.")
            for signal in result.observation_signals:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>{signal.label}</h4>
                        <div class="card-meta">Hazard category: {signal.hazard_category} | Confidence: {signal.confidence}</div>
                        <div>{signal.evidence}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    with controls_tab:
        left, right = st.columns((1.02, 0.98), gap="large")
        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            section_intro("Control Review", "Review points derived from OSHA-style controls and the active field observation.")
            for finding in result.compliance_findings:
                st.markdown(
                    f"""
                    <div class="card">
                        <h4>{finding.rule_title}</h4>
                        <div class="status-tag {status_class(finding.status)}">{finding.status}</div>
                        <div style="margin-top:0.45rem;"><strong>Rationale:</strong> {finding.rationale}</div>
                        <div style="margin-top:0.45rem;"><strong>Review point:</strong> {finding.control_gap}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            section_intro("Corrective Actions", "Prioritized actions for the superintendent, foreman, safety manager, and crew.")
            for item in result.action_plan:
                accent_class = "tag-alert" if item.priority in {"critical", "high"} else "tag-ok"
                st.markdown(
                    f"""
                    <div class="card">
                        <div class="status-tag {accent_class}">{item.priority}</div>
                        <h4 style="margin-top:0.35rem;">{item.action}</h4>
                        <div class="card-meta">Owner: {item.owner} | Timeframe: {item.timeframe}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    with briefing_tab:
        left, right = st.columns((1.0, 1.0), gap="large")
        with left:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            section_intro("Toolbox Talk Points", "Crew-level talking points prepared from the reviewed case.")
            for point in result.toolbox_talk_points:
                st.write(f"- {point}")
            st.markdown("**Escalation note**")
            st.write(result.escalation_note)
            st.markdown("</div>", unsafe_allow_html=True)

        with right:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            section_intro("Report Output", "Export the current review as a markdown brief for portfolio walkthroughs or internal handoff.")
            st.download_button(
                "Download Markdown Report",
                data=report_markdown.encode("utf-8"),
                file_name="agentic-construction-safety-report.md",
                mime="text/markdown",
                width="stretch",
            )
            with st.expander("View generated report"):
                st.code(report_markdown, language="markdown")
            st.markdown("</div>", unsafe_allow_html=True)
