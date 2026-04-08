from __future__ import annotations

from dataclasses import dataclass

from src.knowledge_base import OSHA_RULES
from src.schemas import ActionItem, ComplianceFinding, ObservationSignal, ReasoningAssessment, SafetyAgentRun


@dataclass(frozen=True)
class ObservationContext:
    project_name: str
    contractor_name: str
    work_area: str
    work_type: str
    shift: str
    weather: str
    crew_size: int
    notes: str
    filenames: list[str]


KEYWORD_MAP = {
    "fall": ["fall", "edge", "roof", "unguarded", "ladder", "scaffold", "opening", "elevated"],
    "struck-by": ["forklift", "truck", "crane", "excavator", "loader", "backing", "swing radius"],
    "electrical": ["electrical", "panel", "cord", "temporary power", "energized", "wire"],
    "housekeeping": ["debris", "trip", "blocked", "hose", "cord", "material pile", "clutter"],
    "ppe": ["no hard hat", "no vest", "no glasses", "no gloves", "no helmet", "no ppe", "harness"],
    "excavation": ["trench", "excavation", "spoils", "shoring", "sloping", "cave-in"],
}


def _combined_text(context: ObservationContext) -> str:
    return " ".join(
        [
            context.project_name,
            context.contractor_name,
            context.work_area,
            context.work_type,
            context.shift,
            context.weather,
            context.notes,
            " ".join(context.filenames),
        ]
    ).lower()


def _matched_categories(text: str) -> list[str]:
    matches: list[str] = []
    for category, keywords in KEYWORD_MAP.items():
        if any(keyword in text for keyword in keywords):
            matches.append(category)
    if not matches:
        matches.append("housekeeping")
    return matches


def _build_observation_signals(context: ObservationContext, matched_categories: list[str]) -> list[ObservationSignal]:
    signals: list[ObservationSignal] = []
    note_text = context.notes.strip() or "User did not provide detailed observation notes."

    for category in matched_categories:
        if category == "fall":
            signals.append(
                ObservationSignal(
                    label="Potential fall exposure",
                    evidence=note_text,
                    hazard_category="fall",
                    confidence="high" if any(term in note_text.lower() for term in ["unguarded", "edge", "ladder", "scaffold"]) else "medium",
                )
            )
        elif category == "struck-by":
            signals.append(
                ObservationSignal(
                    label="Worker and equipment interface",
                    evidence=note_text,
                    hazard_category="struck-by",
                    confidence="medium",
                )
            )
        elif category == "electrical":
            signals.append(
                ObservationSignal(
                    label="Temporary power or energized exposure",
                    evidence=note_text,
                    hazard_category="electrical",
                    confidence="medium",
                )
            )
        elif category == "ppe":
            signals.append(
                ObservationSignal(
                    label="PPE control may be missing or unclear",
                    evidence=note_text,
                    hazard_category="ppe",
                    confidence="medium",
                )
            )
        elif category == "excavation":
            signals.append(
                ObservationSignal(
                    label="Excavation protection needs verification",
                    evidence=note_text,
                    hazard_category="excavation",
                    confidence="medium",
                )
            )
        else:
            signals.append(
                ObservationSignal(
                    label="Housekeeping or access condition",
                    evidence=note_text,
                    hazard_category="housekeeping",
                    confidence="medium",
                )
            )

    if context.filenames:
        signals.append(
            ObservationSignal(
                label="Photo evidence attached",
                evidence=f"Uploaded files: {', '.join(context.filenames)}",
                hazard_category="evidence",
                confidence="high",
            )
        )

    return signals


def _build_reasoning(context: ObservationContext, matched_categories: list[str]) -> ReasoningAssessment:
    notes = context.notes.lower()
    severe_terms = ["unguarded", "near miss", "almost fell", "struck", "exposed wire", "open hole", "no harness"]
    risk_level = "moderate"
    if any(term in notes for term in severe_terms):
        risk_level = "critical"
    elif len(matched_categories) >= 2 or context.crew_size >= 6:
        risk_level = "high"

    compounding_factors: list[str] = []
    if context.weather and context.weather.lower() not in {"clear", "indoor", "not provided"}:
        compounding_factors.append(f"Weather adds exposure: {context.weather}.")
    if context.shift.lower() == "night":
        compounding_factors.append("Night work may reduce visibility and communication margins.")
    if context.crew_size >= 6:
        compounding_factors.append("Larger active crew increases coordination risk in the work area.")
    if "wet" in notes or "mud" in notes:
        compounding_factors.append("Walking and climbing surfaces may be less stable than normal.")
    if not compounding_factors:
        compounding_factors.append("No strong compounding factor was explicitly provided, so controls should be verified in the field.")

    escalation_trigger = (
        "Escalate to field leadership now because the scenario suggests immediate exposure that should be controlled before work continues."
        if risk_level in {"high", "critical"}
        else "Keep the issue in active supervision and verify controls during the current shift."
    )

    return ReasoningAssessment(
        risk_summary=(
            f"The observation suggests {', '.join(matched_categories)} exposure in {context.work_area or 'the active work area'}, "
            "with risk driven by current site conditions, worker positioning, and the need for immediate control verification."
        ),
        primary_risk_level=risk_level,
        escalation_trigger=escalation_trigger,
        compounding_factors=compounding_factors,
    )


def _build_compliance_findings(text: str, matched_categories: list[str]) -> list[ComplianceFinding]:
    findings: list[ComplianceFinding] = []
    for rule in OSHA_RULES:
        if rule["hazard_category"] not in matched_categories:
            continue
        triggered = any(keyword in text for keyword in rule["keywords"])
        status = "review needed"
        rationale = "The scenario references this exposure, but the note does not fully confirm whether required controls are in place."
        control_gap = rule["control_hint"]
        if triggered and any(term in text for term in ["no ", "missing", "unguarded", "blocked", "exposed"]):
            status = "likely non-compliant"
            rationale = "The observation text includes indicators that a required safeguard may be missing or degraded."
        elif triggered and any(term in text for term in ["guardrail", "spotter", "barricade", "harness", "protected"]):
            status = "likely compliant"
            rationale = "The observation references at least one control measure that appears relevant to this exposure."

        findings.append(
            ComplianceFinding(
                rule_title=rule["title"],
                status=status,
                rationale=rationale,
                control_gap=control_gap,
            )
        )

    if not findings:
        findings.append(
            ComplianceFinding(
                rule_title="General Duty Review",
                status="review needed",
                rationale="The note is too general to tie to a more specific rule, so the scenario still needs supervisor review.",
                control_gap="Verify task planning, access, PPE, and crew communication before the next work step.",
            )
        )

    return findings


def _build_action_plan(
    context: ObservationContext,
    reasoning: ReasoningAssessment,
    compliance_findings: list[ComplianceFinding],
) -> list[ActionItem]:
    actions: list[ActionItem] = []
    highest_priority = "critical" if reasoning.primary_risk_level == "critical" else "high"
    actions.append(
        ActionItem(
            priority=highest_priority,
            owner="Superintendent",
            action=f"Pause or tightly control work in {context.work_area or 'the affected area'} until the flagged exposure is reviewed.",
            timeframe="Immediately",
        )
    )
    actions.append(
        ActionItem(
            priority="high",
            owner="Safety Manager",
            action="Verify the required controls on site, document the findings, and brief the foreman on what must change before work resumes.",
            timeframe="Today",
        )
    )
    if any(item.status == "likely non-compliant" for item in compliance_findings):
        actions.append(
            ActionItem(
                priority="high",
                owner="Foreman",
                action="Correct the missing safeguard, confirm crew understanding, and record the corrective action in the daily safety log.",
                timeframe="Before next task step",
            )
        )
    actions.append(
        ActionItem(
            priority="medium",
            owner="Crew",
            action="Cover the issue in the next toolbox talk with emphasis on the exact exposure described in the observation.",
            timeframe="Next shift start",
        )
    )
    return actions


def build_demo_agent_run(context: ObservationContext) -> SafetyAgentRun:
    text = _combined_text(context)
    matched_categories = _matched_categories(text)
    observation_signals = _build_observation_signals(context, matched_categories)
    reasoning = _build_reasoning(context, matched_categories)
    compliance_findings = _build_compliance_findings(text, matched_categories)
    action_plan = _build_action_plan(context, reasoning, compliance_findings)

    toolbox_talk_points = [
        "Review the specific exposure before work starts and assign one person to verify the control is actually in place.",
        "Reconfirm who has stop-work authority if the condition changes or the control is removed.",
        "Keep access paths, communication, and worker positioning clear around the active task.",
    ]
    if "fall" in matched_categories:
        toolbox_talk_points.append("Reinforce edge awareness, ladder or scaffold setup, and when fall protection must be active.")
    if "struck-by" in matched_categories:
        toolbox_talk_points.append("Review equipment travel paths, blind spots, and the role of spotters or exclusion zones.")

    return SafetyAgentRun(
        executive_brief=(
            f"{context.project_name or 'This project'} has a {reasoning.primary_risk_level} safety signal in "
            f"{context.work_area or 'the current work area'}. The agent workflow identified "
            f"{len(observation_signals)} structured signals, flagged {len(compliance_findings)} compliance review points, "
            "and produced a prioritized action plan for field leadership."
        ),
        observation_signals=observation_signals,
        reasoning=reasoning,
        compliance_findings=compliance_findings,
        action_plan=action_plan,
        toolbox_talk_points=toolbox_talk_points,
        escalation_note=reasoning.escalation_trigger,
    )
