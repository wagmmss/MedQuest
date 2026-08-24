import type { NextConfig } from "next";
import withPWAInit from "@ducanh2912/next-pwa";

const withPWA = withPWAInit({
  dest: "public",
  disable: process.env.NODE_ENV === "development",
  cacheStartUrl: false,
  dynamicStartUrl: false,
  cacheOnFrontEndNav: false,
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
  typescript: {
    // Typecheck is run during CI and IDE; skipping during container build saves memory and 2+ minutes
    ignoreBuildErrors: true,
  },
  eslint: {
    // Lint is run during CI; skipping during container build saves build time
    ignoreDuringBuilds: true,
  },
  experimental: {
    optimizePackageImports: ["lucide-react", "date-fns", "framer-motion", "recharts"],
  },
};

export default withPWA(nextConfig);

