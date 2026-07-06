type HouseholdIdArg = string | null | undefined

// Appended only when explicitly passed (including `null` for personal scope),
// and always last, so callers that invalidate without a workspace argument
// (e.g. `queryKeys.expenses(monthKey)`) still get a prefix match against every
// workspace-scoped variant instead of missing them.
function withWorkspace<T extends readonly unknown[]>(
  base: T,
  householdId: HouseholdIdArg,
) {
  return householdId !== undefined
    ? ([...base, householdId ?? "personal"] as const)
    : base
}

const queryKeys = {
  all: ["expense-tracker"] as const,
  auth: () => [...queryKeys.all, "auth"] as const,
  currentUser: () => [...queryKeys.auth(), "current-user"] as const,
  workspaces: () => [...queryKeys.all, "workspaces"] as const,
  categories: (householdId?: HouseholdIdArg) =>
    withWorkspace([...queryKeys.all, "categories"] as const, householdId),
  expenses: (monthKey?: string, householdId?: HouseholdIdArg) =>
    withWorkspace(
      monthKey
        ? ([...queryKeys.all, "expenses", monthKey] as const)
        : ([...queryKeys.all, "expenses"] as const),
      householdId,
    ),
  dashboard: (monthKey?: string, householdId?: HouseholdIdArg) =>
    withWorkspace(
      monthKey
        ? ([...queryKeys.all, "dashboard", monthKey] as const)
        : ([...queryKeys.all, "dashboard"] as const),
      householdId,
    ),
  dashboardYearly: (year?: number, householdId?: HouseholdIdArg) =>
    withWorkspace(
      year
        ? ([...queryKeys.all, "dashboard-yearly", year] as const)
        : ([...queryKeys.all, "dashboard-yearly"] as const),
      householdId,
    ),
  budgetSettings: (monthKey?: string) =>
    monthKey
      ? ([...queryKeys.all, "budget-settings", monthKey] as const)
      : ([...queryKeys.all, "budget-settings"] as const),
  recurring: (householdId?: HouseholdIdArg) =>
    withWorkspace([...queryKeys.all, "recurring"] as const, householdId),
  recurringProjection: (monthKey?: string, householdId?: HouseholdIdArg) =>
    withWorkspace(
      monthKey
        ? ([...queryKeys.all, "recurring-projection", monthKey] as const)
        : ([...queryKeys.all, "recurring-projection"] as const),
      householdId,
    ),
  attachments: (expenseId: string) =>
    [...queryKeys.all, "attachments", expenseId] as const,
  attachmentDownloadUrl: (expenseId: string, attachmentId: string) =>
    [...queryKeys.all, "attachments", expenseId, attachmentId, "download-url"] as const,
}

export { queryKeys }
