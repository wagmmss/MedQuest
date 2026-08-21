import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

const MAX_BODY_BYTES = 8 * 1024;
const WEB_VITAL_NAMES = new Set(["CLS", "FCP", "FID", "INP", "LCP", "TTFB"]);

export async function POST(request: Request) {
  const contentLength = Number(request.headers.get("content-length"));
  if (Number.isFinite(contentLength) && contentLength > MAX_BODY_BYTES) {
    return NextResponse.json({ error: "Payload too large" }, { status: 413 });
  }

  const data: unknown = await request.json().catch(() => null);
  if (!data || typeof data !== "object") {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { name, value, rating, path } = data as Record<string, unknown>;
  const numericValue = typeof value === "number" ? value : Number(value);
  if (!WEB_VITAL_NAMES.has(String(name)) || !Number.isFinite(numericValue) || numericValue < 0 || numericValue > 3_600_000) {
    return NextResponse.json({ error: "Invalid web vital" }, { status: 400 });
  }

  console.info(JSON.stringify({
    event: "web_vital",
    name,
    value: Math.round(numericValue * 10_000) / 10_000,
    rating: ["good", "needs-improvement", "poor"].includes(String(rating)) ? rating : undefined,
    path: typeof path === "string" ? path.slice(0, 512) : "unknown",
  }));

  return NextResponse.json({ success: true }, { status: 202 });
}
