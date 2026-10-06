export const MODES = [
  { value: "qa", label: "Q&A" },
  { value: "socratic", label: "Socratic" },
  { value: "evaluator", label: "Evaluator" },
] as const;

export type ModeValue = (typeof MODES)[number]["value"];

export function modeLabel(value: string): string {
  return MODES.find(m => m.value === value)?.label ?? value;
}
