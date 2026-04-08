from __future__ import annotations

from pydantic import BaseModel, Field


class ObservationSignal(BaseModel):
    label: str = Field(description="Short structured signal extracted from the field observation.")
    evidence: str = Field(description="Supporting evidence from the note, image, or job context.")
    hazard_category: str = Field(description="Hazard family such as fall, struck-by, electrical, or housekeeping.")
    confidence: str = Field(description="One of low, medium, or high.")


class ReasoningAssessment(BaseModel):
    risk_summary: str = Field(description="Short plain-English explanation of the combined site risk.")
    primary_risk_level: str = Field(description="One of low, moderate, high, or critical.")
    escalation_trigger: str = Field(description="Why the issue should or should not be escalated.")
    compounding_factors: list[str] = Field(description="Contextual factors that increase the overall risk.")


class ComplianceFinding(BaseModel):
    rule_title: str = Field(description="Short OSHA-style rule or control title.")
    status: str = Field(description="One of likely compliant, review needed, or likely non-compliant.")
    rationale: str = Field(description="Why the observation does or does not appear to satisfy the control.")
    control_gap: str = Field(description="Missing safeguard, unclear item, or next review point.")


class ActionItem(BaseModel):
    priority: str = Field(description="One of critical, high, medium, or low.")
    owner: str = Field(description="Suggested owner such as superintendent, foreman, safety manager, or crew.")
    action: str = Field(description="Operationally useful corrective or preventive action.")
    timeframe: str = Field(description="Expected timing such as immediately, today, or before next shift.")


class SafetyAgentRun(BaseModel):
    executive_brief: str = Field(description="Supervisor-ready summary of the observation and recommended posture.")
    observation_signals: list[ObservationSignal] = Field(description="Structured signals from the observation agent.")
    reasoning: ReasoningAssessment = Field(description="Context-aware risk interpretation from the reasoning agent.")
    compliance_findings: list[ComplianceFinding] = Field(description="Compliance review results from the compliance agent.")
    action_plan: list[ActionItem] = Field(description="Prioritized corrective actions from the planning agent.")
    toolbox_talk_points: list[str] = Field(description="Short safety briefing bullets for the crew.")
    escalation_note: str = Field(description="Supervisor escalation guidance.")
