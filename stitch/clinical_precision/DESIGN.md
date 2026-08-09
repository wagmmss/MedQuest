---
name: Clinical Precision
colors:
  surface: '#f7f9fb'
  surface-dim: '#d8dadc'
  surface-bright: '#f7f9fb'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f4f6'
  surface-container: '#eceef0'
  surface-container-high: '#e6e8ea'
  surface-container-highest: '#e0e3e5'
  on-surface: '#191c1e'
  on-surface-variant: '#424750'
  inverse-surface: '#2d3133'
  inverse-on-surface: '#eff1f3'
  outline: '#737781'
  outline-variant: '#c3c6d1'
  surface-tint: '#335f99'
  primary: '#003466'
  on-primary: '#ffffff'
  primary-container: '#1a4b84'
  on-primary-container: '#93bcfc'
  inverse-primary: '#a6c8ff'
  secondary: '#006a61'
  on-secondary: '#ffffff'
  secondary-container: '#86f2e4'
  on-secondary-container: '#006f66'
  tertiary: '#25354a'
  on-tertiary: '#ffffff'
  tertiary-container: '#3c4c61'
  on-tertiary-container: '#acbcd6'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d5e3ff'
  primary-fixed-dim: '#a6c8ff'
  on-primary-fixed: '#001c3b'
  on-primary-fixed-variant: '#144780'
  secondary-fixed: '#89f5e7'
  secondary-fixed-dim: '#6bd8cb'
  on-secondary-fixed: '#00201d'
  on-secondary-fixed-variant: '#005049'
  tertiary-fixed: '#d3e4fe'
  tertiary-fixed-dim: '#b7c8e1'
  on-tertiary-fixed: '#0b1c30'
  on-tertiary-fixed-variant: '#38485d'
  background: '#f7f9fb'
  on-background: '#191c1e'
  surface-variant: '#e0e3e5'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  gutter: 24px
  margin: 32px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

This design system is built on the principles of **Clinical Modernism**. It prioritizes clarity, reliability, and institutional trust over decorative trends. The aesthetic is "medical-grade"—meaning it is functional, high-fidelity, and sterile without being cold.

The brand personality is authoritative yet empathetic, designed to evoke a sense of safety and precision for healthcare professionals and patients. We lean into a **Corporate / Modern** style characterized by:
- **Information Density:** Carefully managed whitespace to facilitate efficient data scanning.
- **Visual Stability:** A rigid adherence to grid structures and consistent alignment.
- **Precision Detailing:** Micro-interactions and subtle borders that suggest high-end software craftsmanship.

## Colors

The palette is anchored by a sophisticated **Medical Blue** (#1A4B84), a deeper, desaturated tone that conveys institutional longevity. This is supported by a "Clinical Teal" for secondary actions and a rigorous scale of Slate grays for UI structure and typography.

- **Backgrounds:** We utilize a clinical white (#FFFFFF) for the main workspace, with subtle neutral shifts (#F8FAFC) to define sidebar or header areas.
- **Feedback:** Use standard medical semantic colors but desaturated: Red (#B91C1C) for critical errors and Green (#15803D) for success, ensuring they don't clash with the professional primary blue.

## Typography

The design system utilizes **Inter** exclusively to leverage its exceptional legibility and neutral character. To achieve a "high-end" feel, we employ tight letter-spacing on large headings and generous line-heights for body copy to reduce cognitive load during long reading sessions.

Hierarchy is established through weight and color rather than excessive size shifts. Secondary text should always use the `text_secondary` color token to maintain focus on primary information.

## Layout & Spacing

This design system follows a **Fixed-Fluid Hybrid Grid**. Content resides within a maximum container width of 1440px for desktop, centered on the screen to prevent eye strain on ultra-wide monitors.

- **Grid:** A 12-column system with 24px gutters.
- **Rhythm:** An 8px base unit (with a 4px half-step for micro-adjustments) governs all padding and margins. 
- **Density:** We prefer a "Spacious" density profile. Avoid crowding data; use `stack-lg` (32px) to separate logical sections of a medical record or form.

## Elevation & Depth

To maintain a clean, clinical aesthetic, we avoid heavy drop shadows. Instead, we use **Tonal Layering** and **Micro-Shadows**.

- **Surfaces:** Main content sits on Level 0 (White). Sidebars and background surfaces sit on Level -1 (#F8FAFC).
- **Shadows:** Use a single, highly diffused shadow style for cards and floating elements: `0px 1px 3px rgba(0,0,0,0.05), 0px 10px 20px rgba(0,0,0,0.02)`.
- **Borders:** Subtle 1px borders in `border_subtle` are preferred over shadows for defining layout boundaries.

## Shapes

We use a **Soft (4px-6px)** corner radius. This strikes the balance between the clinical precision of sharp corners and the modern friendliness of rounded corners. 

- **Small Components:** Buttons and Inputs use 6px.
- **Large Components:** Cards and Modals use 8px (`rounded-lg`).
- **Interactive States:** Focus rings should follow the component's radius exactly with a 2px offset.

## Components

### Buttons
Primary buttons use the solid `primary_color_hex` with a very subtle top-down linear gradient (e.g., from #245A9D to #1A4B84) to give a tactile, "high-fidelity" feel. Labels are `body-sm` weight 600.

### Input Fields
Inputs utilize a 1px border (#CBD5E1) which darkens to the primary blue on focus. Backgrounds should be pure white. Error states use a soft red tint background with a 1px solid red border.

### Cards
Cards are defined by a 1px `border_subtle` rather than a shadow. They should include a 16px header area with a faint bottom border to separate titles from body content.

### Data Tables
Tables are central to this design system. Use a "Zebra" striping approach with a very faint gray (#F8FAFC) for alternating rows. Headers should be `label-md` with a subtle gray background.

### Chips/Tags
Medical status tags (e.g., "Stable," "Critical") should use desaturated background tints with high-contrast text for maximum readability without being visually loud.