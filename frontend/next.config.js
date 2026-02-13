/** @type {import('next').NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  // Disable static export completely - this is an SSR app
  output: undefined,
  experimental: {
    // Force dynamic rendering
    optimizeCss: false,
  },
};

module.exports = nextConfig;