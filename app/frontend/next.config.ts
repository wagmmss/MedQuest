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
  turbopack: {},
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
