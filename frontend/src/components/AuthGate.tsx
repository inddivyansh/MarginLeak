import React, { FormEvent, useEffect, useState } from 'react';
import { createClient, SupabaseClient, User } from '@supabase/supabase-js';
import { setAccessToken } from '../api/client';

interface AuthGateProps {
  children: React.ReactNode;
}

export interface AuthContextType {
  user: User | null;
  signOut: () => Promise<void>;
}

export const AuthContext = React.createContext<AuthContextType>({
  user: null,
  signOut: async () => {},
});

export const useAuth = () => React.useContext(AuthContext);

export const AuthGate: React.FC<AuthGateProps> = ({ children }) => {

  const [client, setClient] = useState<SupabaseClient | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const validateBackendSession = async (supabase: SupabaseClient, session: { access_token: string; user: User }) => {
    setAccessToken(session.access_token);
    const apiBase = import.meta.env.VITE_API_URL || '/api/v1';
    const response = await fetch(`${apiBase}/auth/me`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
    });
    if (!response.ok) {
      setAccessToken(null);
      await supabase.auth.signOut();
      let errorDetail = 'The backend rejected this session. Verify Supabase credentials and redeploy.';
      try {
        const errorData = await response.json();
        if (errorData.detail) errorDetail = errorData.detail;
      } catch {
        // use fallback message
      }
      throw new Error(errorDetail);
    }
    setUser(session.user);
  };

  useEffect(() => {
    let mounted = true;
    const apiBase = import.meta.env.VITE_API_URL || '/api/v1';
    fetch(`${apiBase}/auth/config`)
      .then((response) => response.json())
      .then(async (config) => {
        if (!config.supabase_url || !config.supabase_anon_key) {
          throw new Error('Supabase authentication is not configured. Add SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_JWT_SECRET.');
        }
        const supabase = createClient(config.supabase_url, config.supabase_anon_key);
        if (!mounted) return;
        setClient(supabase);
        const { data } = await supabase.auth.getSession();
        if (data.session) {
          await validateBackendSession(supabase, data.session);
        }
        setLoading(false);
        supabase.auth.onAuthStateChange((_event, session) => {
          if (!session) {
            setAccessToken(null);
            setUser(null);
            return;
          }
          void validateBackendSession(supabase, session).catch((error) => {
            if (mounted) setMessage(error.message);
          });
        });
      })
      .catch((error) => {
        if (mounted) {
          setMessage(error.message);
          setLoading(false);
        }
      });
    return () => { mounted = false; };
  }, []);

  useEffect(() => {
    if (!client) return;
    const handleExpired = () => client.auth.signOut();
    window.addEventListener('marginleak-auth-expired', handleExpired);
    return () => window.removeEventListener('marginleak-auth-expired', handleExpired);
  }, [client]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!client) return;
    setSubmitting(true);
    setMessage(null);
    const result = mode === 'login'
      ? await client.auth.signInWithPassword({ email, password })
      : await client.auth.signUp({
        email,
        password,
        options: { emailRedirectTo: window.location.origin },
      });
    if (result.error) setMessage(result.error.message);
    else if (mode === 'signup' && !result.data.session) setMessage('Account created. Check your email to confirm the account, then sign in.');
    setSubmitting(false);
  };

  if (loading) return <div className="auth-shell"><div className="auth-panel"><span className="section-kicker">MARGINLEAK</span><h1>Verifying secure workspace</h1><p>Checking your authenticated session...</p></div></div>;
  if (user) {
    return (
      <AuthContext.Provider
        value={{
          user,
          signOut: async () => {
            await client?.auth.signOut();
          },
        }}
      >
        {children}
      </AuthContext.Provider>
    );
  }

  return (
    <div className="auth-shell">
      <form className="auth-panel" onSubmit={submit}>
        <span className="section-kicker">MARGINLEAK</span>
        <h1>{mode === 'login' ? 'Sign in to your audit workspace' : 'Create your private workspace'}</h1>
        <p>Invoices and findings are isolated to your authenticated workspace.</p>
        <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
        <label>Password<input type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required /></label>
        {message && <div className="auth-message">{message}</div>}
        <button className="btn btn-primary" type="submit" disabled={!client || submitting}>{submitting ? 'Working...' : mode === 'login' ? 'Sign In' : 'Create Account'}</button>
        <button className="auth-switch" type="button" onClick={() => setMode(mode === 'login' ? 'signup' : 'login')}>
          {mode === 'login' ? 'Need an account? Create one' : 'Already registered? Sign in'}
        </button>
      </form>
    </div>
  );
};