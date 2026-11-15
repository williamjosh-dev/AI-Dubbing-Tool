import { createNeonAuth } from '@neon/auth/next/server';

export const auth = createNeonAuth({
  baseUrl: process.env.NEON_AUTH_BASE_URL,
  cookies: {
    secret: process.env.BETTER_AUTH_SECRET,
  },
});
