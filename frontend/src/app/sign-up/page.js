import AuthForm from '../components/auth-form';

export const metadata = { title: 'Create an account — Voxa' };

export default function SignUpPage() {
  return <AuthForm mode="sign-up" />;
}
