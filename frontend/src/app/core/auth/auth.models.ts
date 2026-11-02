export interface User {
  id: string;
  email: string;
  plan: string;
  is_admin: boolean;
  created_at: string;
  /** Language for Telegram and other messages sent outside the website. */
  locale: string;
  /** End of the free week; null on Pro and for admins. */
  free_until: string | null;
  /** False once the free week is over: checks and alerts are paused. */
  active: boolean;
}

export interface Session {
  token: string;
  user: User;
  is_new: boolean;
}
