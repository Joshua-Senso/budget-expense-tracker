const queryKeys = {
  all: ["expense-tracker"] as const,
  auth: () => [...queryKeys.all, "auth"] as const,
  currentUser: () => [...queryKeys.auth(), "current-user"] as const,
  workspaces: () => [...queryKeys.all, "workspaces"] as const,
}

export { queryKeys }
