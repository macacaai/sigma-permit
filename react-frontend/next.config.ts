import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Removed output: 'export' to support dynamic API routes
  // This allows the app to run as a regular Next.js server with Caddy
};

export default nextConfig;
