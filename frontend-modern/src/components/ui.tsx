import type {
  ButtonHTMLAttributes,
  HTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";
import type { IconType } from "./teacher/types";

export const cx = (...parts: Array<string | false | null | undefined>) =>
  parts.filter(Boolean).join(" ");

type PanelSize = "sm" | "md" | "lg" | "xl";
type PanelRadius = "panel" | "control" | "card";

const panelPadding: Record<PanelSize, string> = { sm: "p-4", md: "p-5", lg: "p-6", xl: "p-8" };

export const panelClasses = (size: PanelSize = "md", radius: PanelRadius = "panel", stack = true) =>
  cx(
    "border border-line bg-surface",
    radius === "panel" ? "rounded-panel" : radius === "card" ? "rounded-xl" : "rounded-control",
    panelPadding[size],
    stack && "space-y-4",
  );

type PanelProps = HTMLAttributes<HTMLDivElement> & {
  size?: PanelSize;
  radius?: PanelRadius;
  stack?: boolean;
};

export function Panel({
  size = "md",
  radius = "panel",
  stack = true,
  className,
  children,
  ...rest
}: PanelProps) {
  return (
    <div className={cx(panelClasses(size, radius, stack), className)} {...rest}>
      {children}
    </div>
  );
}

type SectionTitleProps = HTMLAttributes<HTMLHeadingElement> & {
  icon?: IconType;
  iconTone?: string;
  tone?: string;
};

export function SectionTitle({
  icon: Icon,
  iconTone = "text-brand-ink",
  tone = "text-fg",
  className,
  children,
  ...rest
}: SectionTitleProps) {
  return (
    <h3
      className={cx("flex items-center gap-2 text-sm font-bold uppercase tracking-wider", tone, className)}
      {...rest}
    >
      {Icon && <Icon className={cx("h-4 w-4", iconTone)} />}
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

export function EmptyNote({
  className = "py-8 text-center",
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  return <p className={cx("text-xs italic text-muted", className)}>{children}</p>;
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <p className="px-3 py-9 text-center text-[13px] leading-[1.6] text-muted">{children}</p>;
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
  md: "p-2.5 rounded-control text-xs",
  header: "px-3 py-1.5 rounded-control text-xs",
  sm: "p-2 rounded-lg",
  xs: "p-1.5 rounded-lg text-xs",
  tiny: "p-1 rounded text-[11px]",
};

const controlBase =
  "border border-line bg-raised focus:border-brand focus:outline-2 focus:outline-brand/30";

type ControlExtras = {
  density?: Density;
  fill?: boolean;
  tone?: string;
};

export function Input({
  density: d = "md",
  fill = true,
  tone = "text-fg",
  className,
  ...rest
}: InputHTMLAttributes<HTMLInputElement> & ControlExtras) {
  return <input className={cx(controlBase, tone, density[d], fill && "w-full", className)} {...rest} />;
}

export function Select({
  density: d = "md",
  fill = true,
  tone = "text-fg",
  className,
  children,
  ...rest
}: SelectHTMLAttributes<HTMLSelectElement> & ControlExtras) {
  return (
    <select className={cx(controlBase, tone, density[d], fill && "w-full", className)} {...rest}>
      {children}
    </select>
  );
}

export function Textarea({
  density: d = "md",
  fill = true,
  tone = "text-fg",
  className,
  ...rest
}: TextareaHTMLAttributes<HTMLTextAreaElement> & ControlExtras) {
  return (
    <textarea className={cx(controlBase, tone, density[d], fill && "w-full", className)} {...rest} />
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
        "cursor-pointer bg-raised text-xs text-muted file:mr-3 file:rounded-xl file:border-0 file:bg-brand file:text-xs file:font-semibold file:text-white",
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
  | "danger"
  | "dangerSoft"
  | "muted";

const variants: Record<ButtonVariant, string> = {
  primary: "border-brand bg-brand text-white hover:bg-brand-hover",
  success: "bg-emerald-600 text-fg hover:bg-emerald-500",
  secondary: "bg-raised text-fg",
  outline: "border border-line bg-raised text-fg",
  surface: "border-line bg-surface text-fg hover:bg-raised",
  ghost: "text-muted",
  link: "text-brand-ink",
  danger: "text-red-400 hover:text-red-300",
  dangerSoft: "border-line bg-surface text-[#f49292] hover:bg-raised",
  muted: "text-muted",
};

type ButtonSize =
  | "bare"
  | "block"
  | "blockLg"
  | "toolbar"
  | "cta"
  | "pill"
  | "mini"
  | "classic"
  | "classicWide"
  | "hero"
  | "walk";

const classicBase = "cursor-pointer gap-2 rounded-md border font-semibold leading-[1.4] no-underline disabled:opacity-45";
const classicFocus =
  "focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#66baff]";

const sizes: Record<ButtonSize, string> = {
  bare: "disabled:opacity-50",
  block: "w-full rounded-control py-2.5 text-xs font-bold disabled:opacity-50",
  blockLg: "w-full rounded-control py-3 text-xs font-bold disabled:opacity-50",
  toolbar: "gap-1.5 rounded-control px-3 py-2 text-xs font-semibold disabled:opacity-50",
  cta: "gap-1.5 rounded-control px-5 py-2 text-xs font-bold shadow-lg disabled:opacity-50",
  pill: "gap-1 rounded-lg px-3 py-1 text-[11px] font-bold disabled:opacity-50",
  mini: "rounded px-2 py-1 text-[10px] font-bold disabled:opacity-50",
  classic: `${classicBase} ${classicFocus} px-4 py-2.5 text-[13px]`,
  classicWide: `${classicBase} ${classicFocus} w-full p-3 text-[13px]`,
  hero: `${classicBase} ${classicFocus} min-w-[174px] px-6 py-3 text-[13px]`,
  walk: `${classicBase} ${classicFocus} px-3 py-[9px] text-xs`,
};

export const buttonClasses = (
  variant: ButtonVariant = "primary",
  size: ButtonSize = "bare",
  extra?: string,
) =>
  cx(
    "inline-flex items-center justify-center transition-[background-color,border-color] duration-150 disabled:cursor-not-allowed",
    variants[variant],
    sizes[size],
    extra,
  );

export function Button({
  variant = "primary",
  size = "bare",
  className,
  type = "button",
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant; size?: ButtonSize }) {
  return (
    <button type={type} className={buttonClasses(variant, size, className)} {...rest}>
      {children}
    </button>
  );
}

export function IconButton({
  danger = false,
  compact = false,
  className,
  type = "button",
  children,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { danger?: boolean; compact?: boolean }) {
  return (
    <button
      type={type}
      className={cx(
        "inline-flex shrink-0 cursor-pointer items-center justify-center rounded-md border border-transparent hover:border-line hover:text-fg focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#66baff]",
        compact ? "size-[27px] bg-transparent" : "size-9 bg-surface",
        danger ? "text-[#f49292]" : "text-muted",
        className,
      )}
      {...rest}
    >
      {children}
    </button>
  );
}

const badgeTones = {
  admin: "bg-[#fff2a8] text-[#463e00]",
  teacher: "bg-[#c7f4db] text-[#145638]",
  inactive: "bg-raised text-muted",
} as const;

export function Badge({ tone, children }: { tone: keyof typeof badgeTones; children: ReactNode }) {
  return (
    <span
      className={cx("rounded px-2 py-1 text-[11px] font-semibold whitespace-nowrap", badgeTones[tone])}
    >
      {children}
    </span>
  );
}

const bannerTones = {
  error: "border-[#f8717140] bg-[#f8717112] text-[#ffb4b4]",
  success: "border-[#34d39940] bg-[#34d39910] text-[#84dbb3]",
} as const;

export function Banner({
  tone,
  children,
  ...rest
}: HTMLAttributes<HTMLParagraphElement> & { tone: keyof typeof bannerTones }) {
  return (
    <p
      className={cx(
        "mb-4 rounded-[7px] border px-4 py-[13px] text-[13px] leading-[1.6]",
        bannerTones[tone],
      )}
      {...rest}
    >
      {children}
    </p>
  );
}

export function MutedText({ className, children, ...rest }: HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cx("my-3 text-xs leading-[1.65] text-muted", className)} {...rest}>
      {children}
    </p>
  );
}

export const formControlClasses =
  "w-full min-w-0 rounded-md border border-line bg-canvas px-3 py-[11px] text-[13px] text-fg focus:border-brand focus:outline-2 focus:outline-brand/30";

export function FormField({
  label,
  className,
  children,
}: {
  label: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <label className={cx("flex flex-col gap-2 text-xs text-muted", className)}>
      {label}
      {children}
    </label>
  );
}

export function FormInput({ className, ...rest }: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cx(formControlClasses, className)} {...rest} />;
}

export function FormSelect({ className, children, ...rest }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select className={cx(formControlClasses, className)} {...rest}>
      {children}
    </select>
  );
}

export const formStackClasses = "flex flex-col gap-5 p-6 text-sm leading-[1.7]";

export function FormStack({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cx(formStackClasses, className)}>{children}</div>;
}

export const studentMainClasses = "mx-auto my-[65px] max-w-[720px] px-5 max-[720px]:my-10";

export const studentPanelClasses =
  "min-w-0 rounded-xl border border-line bg-surface p-[38px] text-center max-[720px]:p-6 [&>p]:my-[18px] [&>p]:text-sm [&>p]:leading-[1.8] [&>p]:text-muted";

export const studentHeadingClasses =
  "my-[18px] text-[32px] leading-[1.25] tracking-[-0.7px] text-fg";

export function DialogFooter({ children }: { children: ReactNode }) {
  return (
    <footer className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-6 py-[18px] max-[720px]:p-4 max-[720px]:[&>button]:px-[11px] max-[720px]:[&>button]:py-[9px] max-[720px]:[&>button]:text-xs">
      {children}
    </footer>
  );
}

export const courseRowClasses = (selected = false) =>
  cx(
    "flex items-center justify-between gap-3 rounded-[9px] border p-3.5",
    selected ? "border-brand bg-[#148bd00c]" : "border-line",
  );

export const shellClasses = "min-h-screen bg-canvas font-ui text-fg";

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
        <tbody className="divide-y divide-line [&>tr]:border-line [&>tr]:bg-raised [&>tr]:text-fg">
          {children}
        </tbody>
      </table>
    </div>
  );
}

export const colorTransition = "transition-[background-color,border-color] duration-150";

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

export const workspaceClasses = (maxWidth: "max-w-[1360px]" | "max-w-[1240px]" = "max-w-[1360px]") =>
  cx("mx-auto px-7 pt-10 pb-[72px] max-[1000px]:px-5 max-[1000px]:pt-7", maxWidth);

export const pageHeadingClasses =
  "mb-7 flex items-center justify-between gap-6 max-[720px]:flex-col max-[720px]:items-start";

export function PageHeading({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: ReactNode;
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <header className={pageHeadingClasses}>
      <div>
        <span className="flex items-center gap-2 text-xs font-semibold text-[#84c9f4]">{eyebrow}</span>
        <h1 className="my-2 text-[30px] tracking-[-0.7px] text-fg max-[720px]:text-[26px]">{title}</h1>
        <p className="text-sm leading-[1.6] text-muted">{description}</p>
      </div>
      {children}
    </header>
  );
}

export const surfacePanelClasses =
  "min-w-0 rounded-xl border border-line bg-surface p-6 max-[720px]:p-[19px]";
