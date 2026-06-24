# Product Requirements Document: Expense Tracker

## 1. Product Overview

Expense Tracker is a private web application for tracking personal expenses, monthly budget health, and spending patterns in Philippine Peso. The app uses social sign-in and persistent cloud storage so each signed-in user can manage their own expenses, categories, recurring costs, installment purchases, and monthly salary settings across devices. Beyond single-user tracking, the app also supports shared household budgeting for invited members, recording and displaying expenses in multiple currencies, and a public landing page that introduces the product to visitors before sign-in.

## 2. Goals

- Help users understand how much they have spent in a selected month.
- Separate credit card spending from other expenses for clearer budget review.
- Track monthly net salary, total spending, remaining balance, and salary usage percentage.
- Support realistic expense patterns including one-time purchases, installment purchases, and recurring monthly costs.
- Allow users to customize categories and category colors.
- Provide Excel import and export for backup, review, and bulk editing workflows.
- Keep expense data private to the authenticated user and to the households they belong to.
- Support shared household budgeting so trusted members can collaborate on a common set of expenses and categories.
- Support multiple currencies so expenses can be recorded and displayed in a user's or household's preferred currency.
- Support user-selectable themes so the app can adapt to different visual preferences, scoped per household for shared accounts and per user for personal accounts.
- Provide a public landing page that explains the product to prospective users before they sign in.

## 3. Target Users

- Primary user: an individual who wants a private personal finance dashboard.
- Secondary users: trusted household members who are invited to collaborate on a shared budget through social sign-in.
- Visitors: prospective users who view the public landing page before deciding to sign in.

## 4. Problem Statement

Personal spending is often spread across several credit cards, monthly bills, online shopping, and ad-hoc expenses. Standard notes or spreadsheets make it difficult to quickly answer: how much was spent this month, which category contributed most, how much salary remains, and what future installments or recurring expenses will affect upcoming months.

Expense Tracker centralizes these workflows in a private dashboard with month-based summaries, category breakdowns, and persistent cloud storage.

## 5. Success Metrics

- A signed-in user can add an expense in under 30 seconds.
- Monthly total, remaining salary, and category breakdown update immediately after create, edit, delete, import, or recurring-expense changes.
- Users can accurately export and re-import expense data without unintended data loss.
- All user data remains isolated by authenticated user identity.
- The app remains usable on desktop and mobile viewports.

## 6. User Stories

- As a user, I want to sign in with a social account (such as Google, GitHub, or Discord) so my tracker is private and available across devices.
- As a user, I want to add one-time expenses with date, description, amount, and category so I can track spending.
- As a user, I want to add installment expenses so future monthly payments are represented automatically.
- As a user, I want to add recurring monthly expenses so bills and subscriptions appear in the correct months.
- As a user, I want to edit or delete expenses so my records stay accurate.
- As a user, I want to manage categories and colors so the tracker matches my accounts and spending types.
- As a user, I want to filter by all expenses, credit card expenses, other expenses, or specific categories so I can inspect focused totals.
- As a user, I want to set a monthly net salary so I can see remaining balance and salary usage.
- As a user, I want to export expenses to Excel so I can keep a backup or review data outside the app.
- As a user, I want to import Excel changes so I can make bulk updates efficiently.
- As a user, I want to attach receipt images to an expense so I keep a visual record of the purchase.
- As a user, I want to create a household and invite trusted members so we can track a shared budget together.
- As a household member, I want to view and add shared expenses and categories so our collaborative budget stays current.
- As a household owner, I want to control who can edit or remove shared data so our records stay trustworthy.
- As a user, I want to record expenses in different currencies so the tracker reflects spending I make abroad or in other currencies.
- As a user, I want to choose a base currency so totals, salary, and remaining balance are summarized consistently.
- As a visitor, I want a public landing page that explains what the tracker does so I can decide whether to sign in.

## 7. Functional Requirements

### 7.1 Authentication

- The app must require social sign-in before showing expense data.
- The app must support multiple social sign-in providers (for example Google, GitHub, and Discord), with the option to add more over time.
- A single user account must be able to link more than one provider identity (so the same person signing in with a different provider resolves to the same account).
- The app must serve a public landing page that is reachable without authentication (see 7.11).
- The unauthenticated state must show the public landing page with a clear path to the private tracker sign-in screen.
- The authenticated state must show the private dashboard.
- The app must support sign out from the profile menu.
- The app should automatically sign out after a period of inactivity.

### 7.2 Expense Management

- Users must be able to create an expense with description, amount, category, expense type, and date.
- Amounts must be positive numbers.
- Dates must use valid `YYYY-MM-DD` values internally.
- Users must be able to edit existing expenses.
- Users must be able to delete single expenses.
- For installment expenses, users must be able to delete either one row or the installment group when supported by the UI.
- Expenses must be associated with the signed-in user.
- Users may attach one or more receipt images to an expense. Attachments are stored in object storage and referenced from the database by key, never stored as binary in the database, and access to an attachment follows the same ownership and household rules as its expense.

### 7.3 Expense Types

- One-time expenses must create one expense row.
- Installment expenses must create one row per term across consecutive months.
- Installment rows must preserve group metadata, installment index, total terms, and original description.
- Recurring monthly expenses must appear in applicable months based on start date, optional end date, and active status.
- Deleting a recurring expense from the monthly view should stop the recurring rule rather than remove generated historical rows.

### 7.4 Categories

- The app must seed default categories for new users.
- Categories must include a name, color, and expense group.
- Supported expense groups are `card` and `other`.
- Users must be able to add, edit, and delete categories.
- Category names must be unique per user.
- Category colors must be valid hex colors.
- The app must prevent deleting the final remaining category.

### 7.5 Budget Tracking

- Users must be able to set monthly net salary for the selected month.
- The app must calculate total spending for the selected month.
- The app must calculate remaining salary as monthly net salary minus monthly total.
- The app must calculate percentage of salary used.
- The app must visually warn when spending reaches a high percentage of salary.
- Salary settings must be stored per user and per month.

### 7.6 Dashboard and Filtering

- The dashboard must show the selected month.
- The dashboard must show credit card expense total and category breakdown.
- The dashboard must show other expense total and category breakdown.
- Users must be able to select a year for yearly overview.
- Users must be able to navigate grouped month windows in the yearly overview.
- Users must be able to filter visible expenses by all expenses, credit card expenses, other expenses, or selected categories.
- Filtered totals must update based on the selected view.

### 7.7 Excel Export

- Users must be able to export expense data to an Excel workbook.
- Exported data must include current expense records and generated recurring entries for the selected year.
- Exported data should include visible user-editable columns and system columns required for reliable re-import.
- Exported file names should include the current date.

### 7.8 Excel Import

- Users must be able to import `.xlsx` or `.xls` files.
- The app must validate imported rows before applying changes.
- The app must report validation errors and avoid partial writes when validation fails.
- The import workflow must support inserts, updates, row deletions, and installment group deletions when represented by the import plan.
- After import, the dashboard must reload user data.

### 7.9 Household Sharing (Multi-Tenancy)

- Users must be able to create a household and become its owner.
- Household owners must be able to invite trusted users by email or account identity, and invitations must require the invited user's authenticated acceptance.
- A user may belong to multiple households and must always retain a personal (non-shared) space.
- Expenses, categories, and recurring expenses must be creatable as either personal or scoped to a specific household.
- Household members must be able to view shared expenses, categories, and recurring expenses for households they belong to.
- Member capabilities (view, add, edit, delete) must be governed by household role.
- Household owners must be able to manage membership and roles, and remove members.
- Removing a member must not delete shared historical rows the household still owns.
- The dashboard must allow switching between personal scope and each household the user belongs to.

### 7.10 Multi-Currency Support

- The app must support recording an expense in a selectable currency.
- Each user, and each household, must have a base currency used for aggregation and summaries.
- The default currency must remain Philippine Peso (PHP).
- The app must convert non-base-currency amounts to the base currency for monthly totals, remaining salary, and salary usage, using a stored exchange rate.
- Both the original entered amount and currency and the converted base-currency amount should be retained for transparency.
- Currency must be validated against the set of supported currency codes.
- Export and import must preserve currency and conversion information.

### 7.11 Public Landing Page

- The app must provide a public landing page reachable without authentication.
- The landing page must describe the product's purpose and key capabilities.
- The landing page must provide a clear social sign-in call to action.
- The landing page must not expose any authenticated user data or privileged functionality.
- After successful sign-in, users must be routed to the private dashboard.

## 8. Non-Functional Requirements

- The app must be responsive across desktop and mobile screens.
- Philippine Peso using `en-PH` and `PHP` is the default currency.
- Currency values must be formatted according to each value's currency code and an appropriate locale, so amounts in other supported currencies display correctly.
- The UI must support multiple visual themes, with a warm dark theme as the default; theme selection is stored per workspace (per user for personal accounts, per household for shared accounts) and applied consistently for everyone in that workspace.
- User actions that mutate data must refresh local dashboard state after successful persistence.
- The app should avoid exposing data before authentication completes.
- Error messages should be actionable where possible.

## 9. Data Requirements

All application records are owned by a `user_id` that references the authenticated user. Identity, linked sign-in providers, and sessions are owned and managed by the authentication framework, not defined by the application (see 9.0).

### 9.0 Identity and sessions (auth-framework owned)

- User identity, linked OAuth provider accounts, and sessions are stored and managed by the authentication framework's own schema; the application must not redefine these tables.
- The application treats the framework's user identifier as the canonical `user_id`, and all application tables reference it.
- A single user must be able to link multiple sign-in providers and resolve to one identity.
- Sessions, tokens, and credentials are handled by the auth layer and are never exposed to the frontend.
- Any additional per-user profile attributes the application needs may extend the framework's user record rather than duplicating it.

### 9.1 `user_categories`

- Stores per-user category definitions.
- Required fields: `user_id`, `name`, `color`, `expense_group`.
- Optional sharing field: `household_id` (set when the category is shared with a household).
- Constraints: non-blank name, valid hex color, valid group, unique category name within its owner scope (per user, or per household when shared).

### 9.2 `expenses`

- Stores one-time and installment expense rows.
- Required fields: `user_id`, `category_id`, `description`, `amount`, `currency`, `spent_on`.
- Optional installment fields: `installment_group_id`, `installment_index`, `installment_total`, `original_description`.
- Optional sharing field: `household_id` (set when the expense belongs to a shared household).
- Optional conversion fields: `base_amount`, `exchange_rate` (used to aggregate non-base-currency amounts).
- Constraints: positive amount, non-blank description, valid currency code, valid installment metadata when grouped.

### 9.3 `recurring_expenses`

- Stores active recurring monthly expense rules.
- Required fields: `user_id`, `category_id`, `description`, `amount`, `currency`, `start_on`, `frequency`, `is_active`.
- Optional fields: `end_on`, `household_id` (set when the rule is shared with a household).
- Supported frequency: monthly.

### 9.4 `user_monthly_settings`

- Stores per-user, per-month budget settings.
- Required fields: `user_id`, `month_key`, `monthly_net_salary`.
- Optional fields: `base_currency` (the user's preferred summary currency; a household's base currency takes precedence when viewing shared scope).
- `month_key` must use `YYYY-MM`.
- Salary must be zero or greater.

### 9.5 Households (auth-framework owned)

- A "household" is the product-facing label for the authentication framework's organization/membership model; the application must not redefine organization, membership, or invitation tables.
- The framework owns the household record, its members, their roles, and the invitation lifecycle (invite, accept, remove).
- Supported member roles are owner and member (additional roles such as admin may be enabled later); each household must retain at least one owner.
- A household must have a base currency used for shared-scope summaries; this may extend the framework's organization record rather than living in a separate table.
- A household's theme preference is stored the same way (extending the organization record) so all members share the household's theme; a personal account's theme is stored on the user's own profile per 9.0.
- A single user may belong to multiple households with a distinct role in each.
- Application tables reference a household by the framework's organization identifier via the optional `household_id` field described in 9.1–9.3.

### 9.6 `expense_attachments`

- Stores references to receipt images held in object storage, not the image bytes themselves.
- Required fields: `expense_id`, `user_id`, `object_key`, `content_type`, `size_bytes`.
- Optional fields: `household_id` (mirrors the parent expense's scope), `uploaded_at`.
- Constraints: each attachment belongs to exactly one expense; the `object_key` is unique; access is governed by the parent expense's ownership and household rules.
- The object store is private; files are never publicly readable and are reached only through short-lived signed URLs issued after an authorization check.

## 10. Privacy and Security Requirements

- Row ownership must be enforced for user-owned and household-shared tables through server-side access controls, with database row-level security applied where appropriate.
- Users must be able to read, insert, update, and delete their own rows, and to access rows belonging to households they are members of, according to their household role.
- Only household owners may delete shared rows or manage household membership; members may read and add shared rows per role policy.
- Expense and recurring-expense writes must only reference categories owned by the authenticated user or shared within a household the user belongs to.
- Household invitations must only be issued by household owners, and joining a household must require the invited user's authenticated acceptance.
- The frontend must never hold database credentials; all data access must go through an authenticated server-side layer.
- Database credentials, OAuth client secrets, and other secret keys must not be committed to the repository.

## 11. UX Requirements

- The unauthenticated screen must clearly explain that the tracker is private.
- Primary dashboard actions must be easy to reach from the top section.
- Add/edit forms must validate required fields before submission.
- Modal dialogs should support Escape to close and restore focus after closing.
- Category colors should appear consistently in filters, breakdown rows, and expense views.
- Empty states should explain when no expenses exist for the selected month or filter.
- The public landing page must communicate the product's value and provide a clear sign-in call to action.
- Shared household expenses and categories should be visually distinguishable from personal ones.
- Each amount should display its currency clearly, and converted base-currency totals should indicate that conversion was applied.
- Household management (invites, members, roles) should be reachable from the profile or settings area.
- Theme selection should be reachable from settings, apply immediately, and follow the active workspace (the personal account or the selected household).

## 12. Out of Scope

- Bank or credit card API integrations.
- Automated receipt scanning or OCR (extracting amounts, dates, or merchants from receipt images). Manually attaching a receipt image to an expense is supported; automatically reading data from it is not.
- Advanced forecasting beyond recurring and installment projection.
- Native mobile apps.
- Public, anonymous household budgeting (sharing is limited to explicitly invited, authenticated members).
- Automated live exchange-rate sourcing (exchange rates are maintained as described in the multi-currency requirements and open questions).

## 13. Risks

- Excel import can cause unintended data changes if system columns are edited incorrectly.
- Client-side import parsing depends on workbook structure remaining stable.
- Recurring generated expenses must be clearly distinguished from persisted expense rows to avoid user confusion.
- Large expense histories may require pagination or server-side aggregation in the future.
- Shared household access expands the access-control surface; misconfigured rules could expose one member's data to another or leak across households.
- Multi-currency aggregation depends on accurate exchange rates; stale or incorrect rates can misstate totals, remaining balance, and salary usage.
- A public landing page increases unauthenticated surface area and must not expose any user data or privileged endpoints.

## 14. Open Questions

- Should users be able to archive categories without deleting their historical expenses?
- Should recurring expenses support weekly, quarterly, or annual frequencies?
- Should the app provide a confirmation preview before applying Excel imports?
- Should budget thresholds be user-configurable instead of fixed warning behavior?
- Should salary be private even from casual screen viewing through an optional hide-values mode?
- How should exchange rates be sourced and updated — manual entry, periodic fetch, or per-expense capture at entry time?
- Should monthly salary be shared at the household level or remain private to each member?
- What household roles are needed beyond owner and member (for example, a view-only role)?
- Should the public landing page be content-managed, or maintained directly in the codebase?

## 15. Release Criteria

- Social sign-in works in local and deployed environments for each enabled provider.
- New users receive default categories after first sign-in.
- Users can create, edit, delete, filter, export, and import expenses.
- Monthly salary, spending, remaining balance, and percentage calculations are correct.
- Recurring and installment expenses appear in expected months.
- Access controls prevent cross-user data access.
- Production build completes successfully.
- Household creation, member invitation, and role-based shared access work end to end.
- Expenses can be recorded in multiple currencies and aggregated correctly into the base currency.
- The public landing page is reachable without authentication and links to social sign-in.
- Access controls prevent cross-household and cross-user data access for both personal and shared rows.
