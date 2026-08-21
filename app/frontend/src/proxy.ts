import { clerkMiddleware } from "@clerk/nextjs/server";
import { NextResponse } from "next/server";

const UUID_V4_REGEX = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export default clerkMiddleware(async (auth, req) => {
  let guestId = req.cookies.get("medquest_guest_session")?.value;
  let isNew = false;

  if (!guestId || !UUID_V4_REGEX.test(guestId) || guestId === "00000000-0000-0000-0000-000000000000") {
    guestId = crypto.randomUUID();
    isNew = true;
  } else {
    guestId = guestId.toLowerCase();
  }

  // Clone request headers and overwrite the internal identity header.
  // Never trust any identity header sent directly from the browser.
  const requestHeaders = new Headers(req.headers);
  requestHeaders.set("x-internal-guest-id", guestId);

  const response = NextResponse.next({
    request: {
      headers: requestHeaders,
    },
  });

  // Persist the cookie on the response if newly created or if not set with exact options
  if (isNew || !req.cookies.has("medquest_guest_session")) {
    response.cookies.set("medquest_guest_session", guestId, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      path: "/",
      maxAge: 60 * 60 * 24 * 365, // 1 year
    });
  }

  return response;
});

export const config = {
  matcher: [
    // Skip Next.js internals and all static files, unless found in search params
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
    // Clerk's Frontend API proxy serves its browser bundle from this path.
    "/__clerk/(.*)",
  ],
};
