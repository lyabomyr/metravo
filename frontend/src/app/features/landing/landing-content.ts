import type { TranslationKey } from '../../core/i18n/locales/en';

/** What the landing page says, as data: the template only lays it out. */

export interface Point {
  icon: string;
  title: TranslationKey;
  text: TranslationKey;
}

export interface UseCase {
  image: string;
  title: TranslationKey;
  text: TranslationKey;
}

export const PROBLEMS: Point[] = [
  { icon: '🔁', title: 'landing.problem.p1.title', text: 'landing.problem.p1.text' },
  { icon: '👯', title: 'landing.problem.p2.title', text: 'landing.problem.p2.text' },
  { icon: '📉', title: 'landing.problem.p3.title', text: 'landing.problem.p3.text' },
];

export const STEPS: Point[] = [
  { icon: '📝', title: 'landing.how.s1.title', text: 'landing.how.s1.text' },
  { icon: '✈️', title: 'landing.how.s2.title', text: 'landing.how.s2.text' },
  { icon: '🔔', title: 'landing.how.s3.title', text: 'landing.how.s3.text' },
];

export const USE_CASES: UseCase[] = [
  { image: 'img/rent.jpg', title: 'landing.cases.rent.title', text: 'landing.cases.rent.text' },
  { image: 'img/buy.jpg', title: 'landing.cases.buy.title', text: 'landing.cases.buy.text' },
  { image: 'img/relocate.jpg', title: 'landing.cases.relocate.title', text: 'landing.cases.relocate.text' },
  { image: 'img/newbuild.jpg', title: 'landing.cases.deals.title', text: 'landing.cases.deals.text' },
];

export const FEATURES: Point[] = [
  { icon: '🧭', title: 'landing.features.f1.title', text: 'landing.features.f1.text' },
  { icon: '🧹', title: 'landing.features.f2.title', text: 'landing.features.f2.text' },
  { icon: '🎯', title: 'landing.features.f3.title', text: 'landing.features.f3.text' },
  { icon: '📉', title: 'landing.features.f4.title', text: 'landing.features.f4.text' },
  { icon: '🗄️', title: 'landing.features.f5.title', text: 'landing.features.f5.text' },
  { icon: '🌍', title: 'landing.features.f6.title', text: 'landing.features.f6.text' },
];

export const FAQ: { question: TranslationKey; answer: TranslationKey }[] = [
  { question: 'landing.faq.q1', answer: 'landing.faq.a1' },
  { question: 'landing.faq.q2', answer: 'landing.faq.a2' },
  { question: 'landing.faq.q3', answer: 'landing.faq.a3' },
  { question: 'landing.faq.q4', answer: 'landing.faq.a4' },
  { question: 'landing.faq.q5', answer: 'landing.faq.a5' },
];

/** The photos are freely licensed from Wikimedia Commons; licences require the credit. */
export const PHOTO_CREDITS = [
  { author: 'Igor123121', license: 'CC BY 4.0', source: 'https://commons.wikimedia.org/wiki/File:J%C3%B3zefa_Dietla_street,_view_to_W,_Kazimierz,_Krak%C3%B3w,_Poland.jpg' },
  { author: 'Lo', license: 'CC0', source: 'https://commons.wikimedia.org/wiki/File:The_living_room_that_needs_houseplants.jpg' },
  { author: 'Panek', license: 'CC BY-SA 4.0', source: 'https://commons.wikimedia.org/wiki/File:19_dzielnica_the_warsaw_hub_skyliner_innogy.jpg' },
  { author: 'Bąblasta Rzecz', license: 'CC BY-SA 3.0', source: 'https://commons.wikimedia.org/wiki/File:Zalasewo,_nowe_osiedle_-_New_apartment_building_(July_2016)_-_panoramio.jpg' },
];
