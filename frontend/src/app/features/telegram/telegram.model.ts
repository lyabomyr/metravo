export interface TelegramLink {
  private_url: string;
  group_url: string;
  expires_at: string;
  /** Adds the bot to a channel; the owner then posts `channel_code` there. */
  channel_url: string;
  channel_code: string;
}

export interface TelegramChat {
  chat_id: string;
  title: string;
  paused: boolean;
  linked_at: string;
  /** True: hears only the searches routed to it; false: every search. */
  only_selected: boolean;
  /** On a search's page: does this chat get that search? */
  receives?: boolean | null;
}
