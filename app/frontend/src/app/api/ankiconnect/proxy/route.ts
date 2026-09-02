import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const targetUrl = body.url || "http://127.0.0.1:8765";

    const ankiPayload: Record<string, unknown> = {
      action: body.action,
      version: body.version || 6,
      params: body.params || {},
    };
    if (body.key) {
      ankiPayload.key = body.key;
    }

    const res = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(ankiPayload),
      signal: AbortSignal.timeout(6000),
    });

    if (!res.ok) {
      return NextResponse.json(
        { error: `AnkiConnect respondeu com status ${res.status}: ${res.statusText}` },
        { status: res.status }
      );
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (error) {
    const msg = error instanceof Error ? error.message : "Falha ao conectar ao AnkiConnect local";
    return NextResponse.json(
      {
        error: "Não foi possível comunicar com o AnkiConnect local no servidor.",
        details: msg,
      },
      { status: 502 }
    );
  }
}
