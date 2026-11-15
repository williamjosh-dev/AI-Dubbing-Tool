import { auth } from './app/auth-server';

export default auth.middleware({ loginUrl: '/sign-in' });

export const config = {
  matcher: ['/dashboard/:path*', '/dubbing/:path*', '/history/:path*', '/feedback/:path*'],
};
