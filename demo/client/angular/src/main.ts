import { bootstrapApplication } from '@angular/platform-browser';
import { provideThemeRuntime } from '@alxarafe/ui-runtime';
import { DEFAULT_THEME } from '@alxarafe/ui-theme-default';
import { ALTERNATIVE_THEME } from '@alxarafe/ui-theme-alternative';
import { CYBERPUNK_THEME } from '@alxarafe/ui-theme-cyberpunk';
import { VINTAGE_THEME } from '@alxarafe/ui-theme-vintage';
import { HIGH_CONTRAST_THEME } from '@alxarafe/ui-theme-high-contrast';
import { DemoApp } from './app';

bootstrapApplication(DemoApp, {
    providers: provideThemeRuntime([
        DEFAULT_THEME, ALTERNATIVE_THEME, CYBERPUNK_THEME, VINTAGE_THEME, HIGH_CONTRAST_THEME,
    ]),
}).catch(error => console.error(error));