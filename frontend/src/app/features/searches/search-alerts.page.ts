import { Component, OnInit, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { TelegramChat } from '../telegram/telegram.model';
import { TelegramApiService } from '../telegram/telegram-api.service';
import { TelegramConnectComponent } from '../telegram/telegram-connect.component';
import { Search } from './search.model';
import { SearchesApiService } from './searches-api.service';

/**
 * Where one search's listings go, at `/searches/:id/notifications` — also the step right after
 * creating a search. Tick existing chats, or connect a chat, group or channel just for it.
 */
@Component({
  selector: 'app-search-alerts-page',
  imports: [ErrorBannerComponent, PageHeaderComponent, RouterLink, TelegramConnectComponent, TranslatePipe],
  template: `
    <app-page-header [title]="'searchAlerts.title' | t: { name: search()?.name ?? '…' }" [subtitle]="'searchAlerts.intro' | t" />
    <app-error-banner [error]="error()" />
    <section class="card stack">
      <h3 class="section-title">Telegram</h3>
      <div class="list">
        @for (chat of chats(); track chat.chat_id) {
          <label class="list__row" data-cy="search-chat">
            <span>
              <b>{{ chat.title || ('searchAlerts.privateChat' | t) }}</b>
              <span class="muted small">
                {{ (chat.only_selected ? 'searchAlerts.selectedSearches' : 'searchAlerts.allSearches') | t }}{{ chat.paused ? ' · ' + ('searchAlerts.paused' | t) : '' }}
              </span>
            </span>
            <input type="checkbox" [checked]="chat.receives" (change)="toggle(chat, $any($event.target).checked)" data-cy="search-chat-toggle" />
          </label>
        } @empty {
          <div class="list__row muted" data-cy="search-chats-none">{{ 'searchAlerts.none' | t }}</div>
        }
      </div>
      <h3 class="section-title">{{ 'searchAlerts.connectNew' | t }}</h3>
      @if (id(); as searchId) {
        <app-telegram-connect [searchId]="searchId" (connected)="load()" />
      }
      <a class="button button--primary button--block" routerLink="/searches" data-cy="search-alerts-done">{{ 'searchAlerts.done' | t }}</a>
    </section>
  `,
})
export class SearchAlertsPage extends BasePage implements OnInit {
  /** Route parameter, bound by `withComponentInputBinding`. */
  readonly id = input.required<string>();

  private readonly searches = inject(SearchesApiService);
  private readonly telegram = inject(TelegramApiService);
  protected readonly search = signal<Search | null>(null);
  protected readonly chats = signal<TelegramChat[]>([]);

  ngOnInit(): void {
    this.run(this.searches.one(this.id()), (search) => this.search.set(search));
    this.load();
  }

  protected load(): void {
    this.run(this.telegram.searchChats(this.id()), (chats) => this.chats.set(chats));
  }

  protected toggle(chat: TelegramChat, receives: boolean): void {
    this.run(this.telegram.route(chat.chat_id, this.id(), receives), (changed) =>
      this.chats.set(this.chats().map((each) => (each.chat_id === changed.chat_id ? changed : each))),
    );
  }
}
