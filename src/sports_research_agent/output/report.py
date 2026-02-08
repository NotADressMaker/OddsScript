from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..extract.schemas import (
    InjuryReport,
    LineMove,
    ProbablePitcher,
    StartingGoalie,
    StarterInfo,
)


@dataclass
class ResearchReport:
    query: str
    generated_at: datetime
    injuries: list[InjuryReport]
    starters: list[StarterInfo]
    goalies: list[StartingGoalie]
    probable_pitchers: list[ProbablePitcher]
    line_moves: list[LineMove]
    notes: list[str]

    def to_json(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "generated_at": self.generated_at.isoformat(),
            "injuries": [item.model_dump() for item in self.injuries],
            "starters": [item.model_dump() for item in self.starters],
            "goalies": [item.model_dump() for item in self.goalies],
            "probable_pitchers": [item.model_dump() for item in self.probable_pitchers],
            "line_moves": [item.model_dump() for item in self.line_moves],
            "notes": self.notes,
        }

    def to_markdown(self) -> str:
        lines = [f"# Sports Research Report", f"Query: {self.query}", ""]
        if self.injuries:
            lines.append("## Injuries")
            for injury in self.injuries:
                lines.append(
                    f"- {injury.player} ({injury.team or 'N/A'}): {injury.status.value}"
                    f" — {injury.snippet} ({injury.source_url})"
                )
        if self.starters:
            lines.append("\n## Starters")
            for starter in self.starters:
                status = "confirmed" if starter.confirmed else "projected"
                lines.append(
                    f"- {starter.player} ({starter.team or 'N/A'}) {starter.role}: {status}"
                    f" — {starter.snippet} ({starter.source_url})"
                )
        if self.goalies:
            lines.append("\n## Goalies")
            for goalie in self.goalies:
                status = "confirmed" if goalie.confirmed else "projected"
                lines.append(
                    f"- {goalie.goalie} ({goalie.team or 'N/A'}): {status}"
                    f" — {goalie.snippet} ({goalie.source_url})"
                )
        if self.probable_pitchers:
            lines.append("\n## Probable Pitchers")
            for pitcher in self.probable_pitchers:
                status = "confirmed" if pitcher.confirmed else "projected"
                lines.append(
                    f"- {pitcher.pitcher} ({pitcher.team or 'N/A'}) vs {pitcher.opponent or 'TBD'}: {status}"
                    f" — {pitcher.snippet} ({pitcher.source_url})"
                )
        if self.line_moves:
            lines.append("\n## Line Moves")
            for move in self.line_moves:
                lines.append(
                    f"- {move.market}: {move.open} → {move.current}"
                    f" — {move.snippet} ({move.source_url})"
                )
        if self.notes:
            lines.append("\n## Notes")
            lines.extend([f"- {note}" for note in self.notes])
        return "\n".join(lines)
