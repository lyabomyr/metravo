import type { Dictionary } from '../en';
import { COMMON } from './common';
import { INTRO } from './intro';
import { LANDING } from './landing';
import { PAGES } from './pages';

export const UK: Dictionary = { ...COMMON, ...LANDING, ...INTRO, ...PAGES };
