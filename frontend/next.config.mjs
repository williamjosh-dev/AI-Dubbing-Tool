/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:5000/api/:path*',
      },
      {
        source: '/outputs/:path*',
        destination: 'http://127.0.0.1:5000/outputs/:path*',
      },
    ];
  },
  experimental: {
    // 100MB specified in bytes (100 * 1024 * 1024)
    proxyClientMaxBodySize: 104857600,
  },
};

export default nextConfig;