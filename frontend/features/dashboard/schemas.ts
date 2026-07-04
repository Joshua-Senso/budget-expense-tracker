export type CategoryBreakdown = {
  category_id: string
  name: string
  color: string
  total: string
}

export type ExpenseGroupBreakdown = {
  total: string
  categories: CategoryBreakdown[]
}

export type DashboardSummaryData = {
  month_key: string
  card: ExpenseGroupBreakdown
  other: ExpenseGroupBreakdown
  month_total: string
  monthly_net_salary: string | null
  remaining: string | null
  percent_used: string | null
}
