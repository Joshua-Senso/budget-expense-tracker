const queryKeys = {
  all: ["expense-tracker"] as const,
  auth: () => [...queryKeys.all, "auth"] as const,
  currentUser: () => [...queryKeys.auth(), "current-user"] as const,
  workspaces: () => [...queryKeys.all, "workspaces"] as const,
  categories: () => [...queryKeys.all, "categories"] as const,
  expenses: (monthKey?: string) =>
    monthKey
      ? ([...queryKeys.all, "expenses", monthKey] as const)
      : ([...queryKeys.all, "expenses"] as const),
  dashboard: (monthKey?: string) =>
    monthKey
      ? ([...queryKeys.all, "dashboard", monthKey] as const)
      : ([...queryKeys.all, "dashboard"] as const),
  dashboardYearly: (year?: number) =>
    year
      ? ([...queryKeys.all, "dashboard-yearly", year] as const)
      : ([...queryKeys.all, "dashboard-yearly"] as const),
  budgetSettings: (monthKey?: string) =>
    monthKey
      ? ([...queryKeys.all, "budget-settings", monthKey] as const)
      : ([...queryKeys.all, "budget-settings"] as const),
  recurring: () => [...queryKeys.all, "recurring"] as const,
  recurringProjection: (monthKey?: string) =>
    monthKey
      ? ([...queryKeys.all, "recurring-projection", monthKey] as const)
      : ([...queryKeys.all, "recurring-projection"] as const),
  attachments: (expenseId: string) =>
    [...queryKeys.all, "attachments", expenseId] as const,
  attachmentDownloadUrl: (expenseId: string, attachmentId: string) =>
    [...queryKeys.all, "attachments", expenseId, attachmentId, "download-url"] as const,
}

export { queryKeys }
