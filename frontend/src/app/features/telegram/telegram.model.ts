export interface TelegramLink {
  private_url: string;
  group_url: string;
  expires_at: string;
}

export interface TelegramChat {
  chat_id: string;
  title: string;
  paused: boolean;
  linked_at: string;
}
