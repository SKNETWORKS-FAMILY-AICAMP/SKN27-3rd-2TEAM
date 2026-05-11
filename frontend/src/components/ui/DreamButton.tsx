import type { ReactNode } from "react";

export type DreamButtonProps = {
  children: ReactNode;
  onClick?: () => void;
  type?: "button" | "submit";
  disabled?: boolean;
  className?: string;
};

export function DreamButton({
  children,
  onClick,
  type = "button",
  disabled = false,
  className = "",
}: DreamButtonProps) {
  const classes = ["dream-button", className].filter(Boolean).join(" ");

  return (
    <button className={classes} type={type} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
}
