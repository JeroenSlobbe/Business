# Project Updates & Changelog

This repository tracks ongoing engineering enhancements, security improvements, and feature developments for the stock portfolio management platform.

---

## 🚀 Engineering Improvements

- Automatically update industry and sector for bonds via `updateStockDataTaskRunner`
- Fixed NYSE new stock insert bug
- Delisting logic now automated
- Addressed `pandas` `.iloc` deprecation warning for financial data parsing
- Fixed divide-by-zero error in dividend calculations
- Excluded warrants from dividend checks (non-dividend assets with `yfinance` limitations)
- Fixed empty array bug in savings calculation logic:
  - If no stocks are procured and no expenses submitted, fallback to `personal_situation[0][3]`
- Added support for multiple statistics pages
- Refactored `fixIndustryID` and `fixSectorID` into separate functions to reduce cyclomatic complexity
- Corrected logic for inserting decimal-based bond quantities
- Fixed Portfolio performance indicator bug
- Improved dividend breakdown graph to show per-share contribution

---

## 🔐 Security Improvements

- Validated JWT signature handling
- Removed import of external JavaScript files to reduce exposure
- Patched two redirect/XSS vulnerabilities


---

## 🧩 Must-Have Features

- Added FIRE dashboard with "what-if" simulation
- Automated dividend and bond interest payouts
- Built enhanced stock screener with query builder
- Added debt import functionality
- Added overview of personal expenses
- Added income tracking and FIRE progress visualization
- Improved dividend graph with breakdown of share contributions

---

## ✨ Nice-to-Have Features Implemented

- Added motivational and financial quotes as a content pack with functional integration
- Enabled support for adding individual ETFs from the XETRA exchange
- Integrated OECD Composite Leading Indicator (CLI) to assess European economic cycles
  - Source: [OECD CLI](https://www.oecd.org/en/data/indicators/composite-leading-indicator-cli.html)

---

## 📦 Stable Release Enhancements

- Developed installation script for streamlined setup:
  - Creates a fresh database
  - Performs initial data pull
  - Fixes exchange onboarding logic
