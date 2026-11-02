import type { Dictionary } from '../en';
import { ADMIN } from './admin';
import { COMMON } from './common';
import { INTRO } from './intro';
import { LANDING } from './landing';
import { PAGES } from './pages';

export const PL: Dictionary = { ...COMMON, ...LANDING, ...INTRO, ...PAGES, ...ADMIN };
