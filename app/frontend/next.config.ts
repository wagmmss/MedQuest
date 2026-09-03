import type { NextConfig } from "next";
import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  // The study screen is the PWA's offline fallback. Its HTML contains only the
  // app shell; questions and attempts remain in IndexedDB/the sync queue.
  // Keeping one cached shell lets the client load the downloaded question pack
  // only after an offline navigation fails.
  cacheStartUrl: false,
  dynamicStartUrl: false,
  // Cache the study shell as soon as the user reaches it. A package download
  // verifies this separately, but this also makes an already-open study screen
  // survive a connection loss before the first package is downloaded.
  cacheOnFrontEndNav: true,
  aggressiveFrontEndNavCaching: false,
  extendDefaultRuntimeCaching: false,
  // The question bank contains thousands of images. Cache them on demand via
  // CacheFirst instead of putting the complete corpus in the install payload.
  publicExcludes: ["!noprecache/**/*", "!images/**/*"],
  customWorkerSrc: "worker",
  workboxOptions: {
    cleanupOutdatedCaches: true,
    skipWaiting: true,
    clientsClaim: true,
    runtimeCaching: [
      {
        urlPattern: ({ sameOrigin, url: { pathname } }: { sameOrigin: boolean; url: { pathname: string } }) =>
          sameOrigin && pathname === "/estudar",
        handler: "NetworkFirst",
        options: {
          cacheName: "medquest-study-shell",
          matchOptions: {
            // A cached shell may safely boot any study filter; the filters and
            // downloaded questions are resolved client-side from IndexedDB.
            ignoreSearch: true,
            // The package download fetches this shell programmatically and a
            // later cold launch is a navigation. Next adds Vary headers to
            // those requests, but both represent this owner-neutral shell.
            ignoreVary: true,
          },
          networkTimeoutSeconds: 3,
          expiration: {
            maxEntries: 1,
            maxAgeSeconds: 60 * 60 * 24 * 30, // 30 dias
          },
        },
      },
      {
        urlPattern: ({ sameOrigin, url: { pathname } }: { sameOrigin: boolean; url: { pathname: string } }) =>
          sameOrigin && pathname.startsWith("/api/images/"),
        handler: "CacheFirst",
        options: {
          cacheName: "medquest-image-cache",
          expiration: {
            maxEntries: 200,
            maxAgeSeconds: 60 * 60 * 24 * 30, // 30 dias
          },
        },
      },
      {
        urlPattern: ({ sameOrigin, url: { pathname } }: { sameOrigin: boolean; url: { pathname: string } }) =>
          sameOrigin && pathname.startsWith("/api/"),
        handler: "NetworkOnly",
      },
    ],
  },
});

const nextConfig: NextConfig = {
  output: "standalone",
  turbopack: {},
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
        ],
      },
    ];
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "img.clerk.com",
        pathname: "/**",
      },
    ],
  },
  experimental: {
    optimizePackageImports: ["lucide-react", "date-fns", "framer-motion", "recharts"],
  },
};

export default withPWA(nextConfig);
