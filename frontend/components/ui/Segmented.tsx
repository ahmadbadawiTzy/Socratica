import { cn } from "@/lib/cn";

export interface SegmentedOption {
  value: string;
  label: string;
}

export default function Segmented({
  value,
  onChange,
  options,
  ariaLabel,
  className,
}: {
  value: string;
  onChange: (value: string) => void;
  options: readonly SegmentedOption[];
  ariaLabel: string;
  className?: string;
}) {
  return (
    <div
      role="group"
      aria-label={ariaLabel}
      className={cn(
        "inline-flex items-center rounded-md border border-line bg-panel-strong p-0.5 text-xs",
        className
      )}
    >
      {options.map((option) => {
        const active = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(option.value)}
            className={cn(
              "rounded px-2.5 py-1 font-medium transition",
              active
                ? "bg-panel text-ink shadow-2xs border border-line font-semibold"
                : "text-muted hover:text-ink"
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
