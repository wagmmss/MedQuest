import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const BACKEND_URL = process.env.FLASK_API_URL || process.env.NEXT_PUBLIC_FLASK_API_URL || "https://medquest-api.onrender.com";

async function handler(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const targetUrl = `${BACKEND_URL}/api/${path.join("/")}${req.nextUrl.search}`;

  const { getToken } = await auth();
  const token = await getToken();

  const headers = new Headers(req.headers);
  headers.delete("host");
  // CRITICAL: Prevent backend from sending compressed data, let Vercel handle it
  headers.delete("accept-encoding");
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  console.log(`[PROXY] Forwarding ${req.method} request to: ${targetUrl}`);

  try {
    const response = await fetch(targetUrl, {
      method: req.method,
      headers,
      body: req.method !== "GET" && req.method !== "HEAD" ? await req.blob() : undefined,
      redirect: "manual",
    });

    console.log(`[PROXY] Received response from backend: ${response.status} ${response.statusText}`);

    const responseHeaders = new Headers(response.headers);
    // CRITICAL: If the backend still sends compressed data, strip the headers so Vercel computes the correct size
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
      headers: { "Content-Type": "application/json" }
    });
  }
}

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const PATCH = handler;
export const DELETE = handler;
export const OPTIONS = handler;
