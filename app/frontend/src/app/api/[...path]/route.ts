import { NextRequest, NextResponse } from "next/server";
import { auth } from "@clerk/nextjs/server";

const BACKEND_URL = process.env.FLASK_API_URL || "http://127.0.0.1:5000";

export async function ANY(req: NextRequest, { params }: { params: Promise<{ path: string[] }> }) {
  const { path } = await params;
  const targetUrl = `${BACKEND_URL}/api/${path.join("/")}${req.nextUrl.search}`;

  const { getToken } = await auth();
  const token = await getToken();

  const headers = new Headers(req.headers);
  headers.delete("host");
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(targetUrl, {
    method: req.method,
    headers,
    body: req.method !== "GET" && req.method !== "HEAD" ? await req.blob() : undefined,
    redirect: "manual",
  });

  const responseHeaders = new Headers(response.headers);
  responseHeaders.delete("content-encoding");

  return new NextResponse(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}

export const GET = ANY;
export const POST = ANY;
export const PUT = ANY;
export const PATCH = ANY;
export const DELETE = ANY;
export const OPTIONS = ANY;
