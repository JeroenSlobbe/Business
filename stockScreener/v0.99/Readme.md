# Project Updates & Changelog

This repository tracks ongoing engineering enhancements, security improvements, and feature developments for the stock portfolio management platform.

---

## 🚀 Engineering Improvements

- Modularized database logic by moving DB handling out of `logic.py`
- Introduced a dedicated data layer to simplify integration of alternative data sources
- Hardened `securityFilter` logic to prevent stock history injection issues:
  - Improved sanitization and filtering for malformed or incomplete financial entries
  - Handled edge cases with `NaN`, `None`, `inf`, or zero values that triggered security violations
- Fixed BWSN view rendering bug
- Introduced centralized configuration file support
- Added DB indexes to boost performance on stock profile queries
- Updated `yfinance` to latest version to bypass previous request blocks
- Implemented hourly token refresh for stock data refresher
- Corrected dividend table layout and % calculations
- Handled status field for special/active states properly
- Enhanced insert logic for `stock` and `bond` asset types
- Investigated multi-stock request batching to bypass rate limits (no viable solution yet for detailed stats)
- Ensured bonds are included in updates (using `regularMarketPrice`)
- Added token refresh handling for data fetch error pages
- Fixed GDP growth parsing bug
- Corrected input filters and region-specific naming bugs ("ams and brussels")

---

## 🔐 Security Improvements

- Implemented strict input validation across all endpoints
- Fixed input parsing issues with newline and comma-separated strategic evaluations
- Enforced secure headers for web responses
- Upgraded authentication to JWT via `dataapp`

---

## 🧩 Must-Have Features

- Made stock profiles fully editable from the frontend
- Enabled daily auto-refresh for portfolio-held stocks
- Improved CSS for better UI/UX consistency
- Automated dividend expectation calculations
- Added manual bond creation interface
- Generated portfolio stats: currency & geographic exposure, asset type % breakdowns
- In-page updates for dividend expectations and payout tracking
- Added view of stock purchase conditions
- Full support added for ETFs

---
