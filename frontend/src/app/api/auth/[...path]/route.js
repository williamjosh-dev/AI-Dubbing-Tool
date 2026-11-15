import { auth } from '../../../auth-server';

export const { GET, POST, PUT, PATCH, DELETE } = auth.handler();
