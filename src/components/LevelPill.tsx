import { usePrefs } from "../lib/prefs";
import { LEVELS } from "../lib/vitality";
import type { VitalityLevel } from "../types";

export default function LevelPill({ level }: { level: VitalityLevel }) {
  const { level: label } = usePrefs();
  return (
    <span className="level">
      <span className="dot" style={{ background: LEVELS[level].color }} />
      {level} {label(level)}
    </span>
  );
}
