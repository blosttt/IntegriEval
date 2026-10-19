import type {
  ButtonHTMLAttributes,
  HTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";
import type { IconType } from "./types";

export const cx = (...parts: Array<string | false | null | undefined>) =>
  parts.filter(Boolean).join(" ");

type PanelProps = HTMLAttributes<HTMLDivElement> & {

  size?: "sm" | "md" | "lg" | "xl";

  radius?: "panel" | "control";

  stack?: boolean;
};

const panelPadding = { sm: "p-4", md: "p-5", lg: "p-6", xl: "p-8" } as const;

export function Panel({
  size = "md",
  radius = "panel",
  stack = true,
  className,
  children,
  ...rest
}: PanelProps) {
  return (
    <div
      className={cx(
        "border border-line bg-surface",
        radius === "panel" ? "rounded-panel" : "rounded-control",
        panelPadding[size],
        stack && "space-y-4",
        className,
      )}
      {...rest}
    >
      {children}
    </div>
  );
}

export const panelClass = "rounded-panel border border-line bg-surface p-6 space-y-4";

type SectionTitleProps = HTMLAttributes<HTMLHeadingElement> & {
  icon?: IconType;

  iconClassName?: string;
};

export function SectionTitle({
  icon: Icon,
  iconClassName = "text-brand-ink",
  className,
  children,
  ...rest
}: SectionTitleProps) {
  return (
    <h3
      className={cx(
        "flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-fg",
        className,
      )}
      {...rest}
    >
      {Icon && <Icon className={cx("h-4 w-4", iconClassName)} />}
      {children}
    </h3>
  );
}

export function Hint({ className, children, ...rest }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cx("text-xs text-muted", className)} {...rest}>
      {children}
    </p>
  );
}

export function EmptyNote({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <p className={cx("py-8 text-center text-xs italic text-muted", className)}>{children}</p>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="px-3 py-9 text-center text-[13px] leading-relaxed text-muted">{children}</p>;
}

export function ReadOnlyNote({ children }: { children: ReactNode }) {
  return (
    <div className="col-span-full rounded-md border border-l-[3px] border-line border-l-brand bg-surface px-[18px] py-3.5 text-[13px] leading-[1.7] text-muted">
      {children}
    </div>
  );
}

export function Field({
  label,
  children,
  className,
}: {
  label: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <label className={cx("block", className)}>
      <span className="mb-1 block font-bold text-fg">{label}</span>
      {children}
    </label>
  );
}

type Density = "md" | "header" | "sm" | "xs" | "tiny";

const density: Record<Density, string> = {
  md: "p-2.5 rounded-control",
  header: "px-3 py-1.5 rounded-control",
  sm: "p-2 rounded-lg",
  xs: "p-1.5 rounded-lg",
  tiny: "p-1 rounded",
};

const controlBase =
  "border border-line bg-raised text-xs text-fg focus:border-brand focus:outline-2 focus:outline-brand/30";

type ControlExtras = {

  density?: Density;

  fill?: boolean;
};

export function Input({
  density: d = "md",
  fill = true,
  className,
  ...rest
}: InputHTMLAttributes<HTMLInputElement> & ControlExtras) {
  return <input className={cx(controlBase, density[d], fill && "w-full", className)} {...rest} />;
}

export function Select({
  density: d = "md",
  fill = true,
  className,
  children,
  ...rest
}: SelectHTMLAttributes<HTMLSelectElement> & ControlExtras) {
  return (
    <select className={cx(controlBase, density[d], fill && "w-full", className)} {...rest}>
      {children}
    </select>
  );
}

export function Textarea({
  density: d = "md",
  fill = true,
  className,
  ...rest
}: TextareaHTMLAttributes<HTMLTextAreaElement> & ControlExtras) {
  return (
    <textarea className={cx(controlBase, density[d], fill && "w-full", className)} {...rest} />
  );
}

export function FileInput({
  large = false,
  className,
  ...rest
}: Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & { large?: boolean }) {
  return (
    <input
      type="file"
      className={cx(
        "cursor-pointer text-xs text-muted file:mr-3 file:rounded-control file:border-0 file:bg-brand file:text-xs file:font-semibold file:text-white hover:file:bg-brand-hover",
        large ? "file:px-4 file:py-2.5" : "file:px-3 file:py-2",
        className ?? "w-full",
      )}
      {...rest}
    />
  );
}

type ButtonVariant =
  | "primary"
  | "success"
  | "secondary"
  | "outline"
  | "surface"
  | "ghost"
  | "link"
  | "danger";

const variants: Record<ButtonVariant, string> = {
  primary: "bg-brand text-white hover:bg-brand-hover",
  success: "bg-emerald-600 text-white hover:bg-emerald-500",
  secondary: "bg-raised text-fg hover:bg-line",
  outline: "border border-line bg-raised text-fg hover:bg-line",
  surface: "border border-line bg-surface text-fg hover:bg-raised",
  ghost: "text-muted hover:text-fg",
  link: "text-brand-ink",
  danger: "text-red-400 hover:text-red-300",
};

export const btnBlock = "w-full rounded-control py-2.5 text-xs font-bold";
export const btnBlockLg = "w-full rounded-control py-3 text-xs font-bold";
export const btnToolbar = "rounded-control px-3 py-2 text-xs font-semibold";
export const btnPill = "rounded-lg px-3 py-1 text-[11px] font-bold";
export const btnClassic = "rounded-md px-4 py-2.5 text-[13px] font-semibold";
export const btnIcon = "p-1";

export function Button({
  variant = "primary",
  className,
  type = "button",
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }) {
  return (
    <button
      type={type}
      className={cx(
        "inline-flex items-center justify-center gap-1.5 transition-colors disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}

type TableColumn = string | { label: string; align?: "left" | "right" };

export function DataTable({
  columns,
  headPadding = "pb-3",
  children,
}: {
  columns: TableColumn[];
  headPadding?: "pb-2" | "pb-3";
  children: ReactNode;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs">
        <thead>
          <tr className="border-b border-line text-muted">
            {columns.map((column) => {
              const { label, align } =
                typeof column === "string" ? { label: column, align: "left" as const } : column;
              return (
                <th key={label} className={cx(headPadding, align === "right" && "text-right")}>
                  {label}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody className="divide-y divide-line">{children}</tbody>
      </table>
    </div>
  );
}

export const rowClass = "bg-raised";

export const selectableCard = (selected: boolean, padding = "p-4") =>
  cx(
    "cursor-pointer rounded-control border transition-all",
    padding,
    selected ? "border-brand bg-brand-soft ring-1 ring-brand" : "border-line bg-raised",
  );

export function ModalFrame({
  maxWidth = "max-w-lg",
  className,
  children,
}: {
  maxWidth?: "max-w-lg" | "max-w-3xl";
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-4">
      <div
        className={cx(
          "w-full rounded-panel border border-line bg-raised p-6 text-xs",
          maxWidth,
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}
