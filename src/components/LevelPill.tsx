import { LEVELS } from "../lib/vitality";
import type { VitalityLevel } from "../types";

export default function LevelPill({ level }: { level: VitalityLevel }) {
  const meta = LEVELS[level];
  return (
    <span className="level">
      <span className="dot" style={{ background: meta.color }} />
      {level} {meta.label}
    </span>
  );
}
