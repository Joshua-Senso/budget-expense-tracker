const queryKeys = {
  all: ["expense-tracker"] as const,
  auth: () => [...queryKeys.all, "auth"] as const,
  currentUser: () => [...queryKeys.auth(), "current-user"] as const,
  workspaces: () => [...queryKeys.all, "workspaces"] as const,
  categories: () => [...queryKeys.all, "categories"] as const,
  expenses: () => [...queryKeys.all, "expenses"] as const,
  dashboard: () => [...queryKeys.all, "dashboard"] as const,
}

export { queryKeys }
