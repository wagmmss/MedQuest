import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";
import { getGuestSession } from "@/lib/session";

const BACKEND_URL = process.env.FLASK_API_URL || process.env.NEXT_PUBLIC_FLASK_API_URL || "https://medquest-api.onrender.com";

async function handler(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const proxySecret = process.env.FLASK_API_PROXY_SECRET;
  if (!proxySecret) {
    console.error("[PROXY] FLASK_API_PROXY_SECRET is not configured on the server.");
    return new NextResponse(
      JSON.stringify({ error: "Server configuration error: missing internal proxy secret" }),
      {
        status: 500,
        headers: { "Content-Type": "application/json" },
      }
    );
  }

  const { path } = await params;
  const targetUrl = `${BACKEND_URL}/api/${path.join("/")}${req.nextUrl.search}`;

  const { getToken } = await auth();
  const token = await getToken();
  const guestId = await getGuestSession();

  const headers = new Headers(req.headers);
  headers.delete("host");
  // Prevent backend from sending compressed data, let Next/Vercel handle compression
  headers.delete("accept-encoding");

  // Remove untrusted or spoofable client-supplied auth headers
  headers.delete("authorization");
  headers.delete("x-guest-id");
  headers.delete("x-internal-proxy-token");
  headers.delete("x-internal-guest-id");

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  } else if (guestId) {
    headers.set("X-Guest-ID", guestId);
  }

  headers.set("X-Internal-Proxy-Token", proxySecret);

  try {
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: req.method !== "GET" && req.method !== "HEAD" ? await req.blob() : undefined,
      redirect: "manual",
    });

    const responseHeaders = new Headers(response.headers);
    responseHeaders.delete("content-encoding");
    responseHeaders.delete("content-length");

    return new NextResponse(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown error";
    console.error(`[PROXY] Fetch error to ${targetUrl}:`, message);
    return new NextResponse(JSON.stringify({ error: "Proxy fetch failed", details: message }), {
      status: 502,
      headers: { "Content-Type": "application/json" },
    });
  }
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
export const OPTIONS = handler;
