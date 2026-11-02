import { Component, OnInit, inject, signal } from '@angular/core';

import { WhenPipe } from '../../core/i18n/format.pipes';
import { LanguageSwitcherComponent } from '../../core/i18n/language-switcher.component';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BillingApiService, Plan } from '../billing/billing-api.service';
import { PlanCardComponent } from '../billing/plan-card.component';
import { FAQ, FEATURES, PHOTO_CREDITS, PROBLEMS, STEPS, USE_CASES } from './landing-content';
import { PhoneDemoComponent } from './phone-demo.component';
import { SignInCardComponent } from './sign-in-card.component';

/** The front door: what Metravo solves, how it works, prices — and the sign-in form. */
@Component({
  selector: 'app-landing-page',
  imports: [LanguageSwitcherComponent, PhoneDemoComponent, PlanCardComponent, SignInCardComponent, TranslatePipe, WhenPipe],
  templateUrl: './landing.page.html',
  styleUrl: './landing.page.css',
})
export class LandingPage implements OnInit {
  private readonly billing = inject(BillingApiService);

  protected readonly problems = PROBLEMS;
  protected readonly steps = STEPS;
  protected readonly cases = USE_CASES;
  protected readonly features = FEATURES;
  protected readonly faq = FAQ;
  protected readonly credits = PHOTO_CREDITS;
  protected readonly plans = signal<Plan[]>([]);

  ngOnInit(): void {
    this.billing.plans().subscribe((plans) => this.plans.set(plans));
  }

  protected toStart(): void {
    document.getElementById('start')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => document.querySelector<HTMLInputElement>('#start input')?.focus(), 400);
  }
}
