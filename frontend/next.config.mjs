/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.BACKEND_URL}/api/:path*`,
      },
      {
        source: '/outputs/:path*',
        destination: `${process.env.BACKEND_URL}/outputs/:path*`,
      },
    ];
  },
  experimental: {
    // 100MB specified in bytes (100 * 1024 * 1024)
    proxyClientMaxBodySize: 104857600,
  },
};

export default nextConfig;