import type * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Small line icons drawn in the strawberry → orange gradient chips, matching
 * the feature-card icons on strawberry.rocks.
 */
function Icon({ children }: { children: React.ReactNode }) {
	return (
		<svg
			viewBox="0 0 24 24"
			fill="none"
			stroke="currentColor"
			strokeWidth={2}
			strokeLinecap="round"
			strokeLinejoin="round"
			className="size-4"
			aria-hidden="true"
		>
			{children}
		</svg>
	);
}

export const Icons = {
	bolt: (
		<Icon>
			<path d="M13 2 4.1 12.7a.7.7 0 0 0 .5 1.1H11l-1 8.2 8.9-10.7a.7.7 0 0 0-.5-1.1H12l1-8.2Z" />
		</Icon>
	),
	signal: (
		<Icon>
			<path d="M4.9 19.1a10 10 0 0 1 0-14.2M7.8 16.2a6 6 0 0 1 0-8.4M16.2 7.8a6 6 0 0 1 0 8.4M19.1 4.9a10 10 0 0 1 0 14.2" />
			<circle cx="12" cy="12" r="1.5" fill="currentColor" stroke="none" />
		</Icon>
	),
	stream: (
		<Icon>
			<path d="M22 12h-4l-3 9L9 3l-3 9H2" />
		</Icon>
	),
	plug: (
		<Icon>
			<path d="M12 22v-5M9 7V2M15 7V2M6 13V8h12v5a4 4 0 0 1-4 4h-4a4 4 0 0 1-4-4Z" />
		</Icon>
	),
	database: (
		<Icon>
			<ellipse cx="12" cy="5" rx="9" ry="3" />
			<path d="M3 5v14a9 3 0 0 0 18 0V5M3 12a9 3 0 0 0 18 0" />
		</Icon>
	),
	layers: (
		<Icon>
			<path d="m12 2 9 5-9 5-9-5 9-5ZM3 12l9 5 9-5M3 17l9 5 9-5" />
		</Icon>
	),
	code: (
		<Icon>
			<path d="m16 18 6-6-6-6M8 6l-6 6 6 6" />
		</Icon>
	),
};

/** A test panel styled like a strawberry.rocks feature card. */
export function TestCard({
	title,
	icon,
	children,
}: {
	title: string;
	icon?: React.ReactNode;
	children: React.ReactNode;
}) {
	return (
		<section className="flex flex-col gap-4 rounded-2xl border border-g-100 bg-white/70 p-5 backdrop-blur-sm">
			<div className="flex items-center gap-3">
				{icon && (
					<span className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-magenta to-orange text-white shadow-sm">
						{icon}
					</span>
				)}
				<h2 className="font-display text-lg font-bold tracking-tight text-ink">
					{title}
				</h2>
			</div>
			{children}
		</section>
	);
}

const STATUS_STYLES: Record<string, string> = {
	idle: "bg-g-50 text-g-700",
	loading: "bg-orange/10 text-orange",
	complete: "bg-green/10 text-green",
	error: "bg-strawberry/10 text-strawberry",
};

/**
 * Status pill. The DOM text stays the raw lowercase status (e.g. "complete")
 * so Playwright assertions keep matching — only the display is capitalized.
 */
export function StatusBadge({
	status,
	testId,
}: {
	status: string;
	testId?: string;
}) {
	return (
		<span
			data-testid={testId}
			className={cn(
				"inline-flex w-fit items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold capitalize",
				STATUS_STYLES[status] ?? STATUS_STYLES.idle,
			)}
		>
			<span
				className={cn(
					"size-1.5 rounded-full bg-current",
					status === "loading" && "animate-pulse",
				)}
			/>
			{status}
		</span>
	);
}

/** A dark "code editor" window for JSON responses, like the website hero. */
export function ResultBlock({
	children,
	testId,
	label = "Response",
}: {
	children: React.ReactNode;
	testId?: string;
	label?: string;
}) {
	return (
		<div className="overflow-hidden rounded-xl border border-g-900 bg-ink shadow-md">
			<div className="flex items-center gap-2 border-b border-white/10 px-4 py-2.5">
				<span className="size-3 rounded-full bg-[#ff5f56]" />
				<span className="size-3 rounded-full bg-[#ffbd2e]" />
				<span className="size-3 rounded-full bg-[#27c93f]" />
				<span className="ml-2 font-mono text-xs text-white/40">{label}</span>
			</div>
			<pre
				data-testid={testId}
				className="max-h-80 overflow-auto p-4 font-mono text-sm leading-relaxed text-g-50"
			>
				{children}
			</pre>
		</div>
	);
}

export function ErrorBanner({
	message,
	testId,
}: {
	message: string;
	testId?: string;
}) {
	return (
		<p
			data-testid={testId}
			className="flex items-start gap-2 rounded-xl border border-strawberry/30 bg-strawberry/10 px-4 py-3 text-sm font-medium text-strawberry"
		>
			<span aria-hidden="true">⚠</span>
			<span>{message}</span>
		</p>
	);
}

/** Inline spinner row used while a query/subscription is in flight. */
export function LoadingRow({
	children = "Loading…",
	testId,
}: {
	children?: React.ReactNode;
	testId?: string;
}) {
	return (
		<div
			data-testid={testId}
			className="flex items-center gap-2 text-sm font-medium text-g-700"
		>
			<span className="size-4 animate-spin rounded-full border-2 border-g-100 border-t-strawberry" />
			{children}
		</div>
	);
}
