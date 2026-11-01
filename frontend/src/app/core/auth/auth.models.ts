export interface User {
  id: string;
  email: string;
  plan: string;
  is_admin: boolean;
  created_at: string;
}

export interface Session {
  token: string;
  user: User;
  is_new: boolean;
}
