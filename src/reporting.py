from __future__ import annotations

from datetime import date

from src.agent_workflow import ObservationContext
from src.schemas import SafetyAgentRun


def build_markdown_report(
    result: SafetyAgentRun,
    *,
    context: ObservationContext,
    observation_date: date,
) -> str:
    lines = [
        "# Agentic Construction Safety Copilot Report",
        "",
        f"- Project: {context.project_name or 'Not provided'}",
        f"- Contractor: {context.contractor_name or 'Not provided'}",
        f"- Work area: {context.work_area or 'Not provided'}",
        f"- Work type: {context.work_type or 'Not provided'}",
        f"- Shift: {context.shift or 'Not provided'}",
        f"- Weather: {context.weather or 'Not provided'}",
        f"- Crew size: {context.crew_size}",
        f"- Observation date: {observation_date.isoformat()}",
        "",
        "## Executive Brief",
        result.executive_brief,
        "",
        "## Observation Agent",
    ]

    for signal in result.observation_signals:
        lines.extend(
            [
                f"- {signal.label} [{signal.hazard_category} | confidence: {signal.confidence}]",
                f"  Evidence: {signal.evidence}",
            ]
        )

    lines.extend(
        [
            "",
            "## Reasoning Agent",
            f"- Primary risk level: {result.reasoning.primary_risk_level}",
            f"- Risk summary: {result.reasoning.risk_summary}",
            f"- Escalation trigger: {result.reasoning.escalation_trigger}",
            "",
            "### Compounding Factors",
        ]
    )
    for factor in result.reasoning.compounding_factors:
        lines.append(f"- {factor}")

    lines.extend(["", "## Compliance Agent"])
    for finding in result.compliance_findings:
        lines.extend(
            [
                f"### {finding.rule_title}",
                f"- Status: {finding.status}",
                f"- Rationale: {finding.rationale}",
                f"- Control gap: {finding.control_gap}",
                "",
            ]
        )

    lines.append("## Planning Agent")
    for item in result.action_plan:
        lines.append(f"- [{item.priority}] {item.owner} | {item.timeframe} | {item.action}")

    lines.extend(["", "## Toolbox Talk Points"])
    for point in result.toolbox_talk_points:
        lines.append(f"- {point}")

    lines.extend(["", "## Escalation Note", result.escalation_note, ""])
    return "\n".join(lines)
