/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) return [];

    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/api/:path*`,
      },
      {
        source: '/outputs/:path*',
        destination: `${backendUrl}/outputs/:path*`,
      },
    ];
  },
  experimental: {
    // 100MB specified in bytes (100 * 1024 * 1024)
    proxyClientMaxBodySize: 104857600,
  },
};

export default nextConfig;
