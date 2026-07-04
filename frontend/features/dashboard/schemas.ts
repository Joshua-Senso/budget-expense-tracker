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

export type MonthlyOverview = {
  month_key: string
  month: number
  card_total: string
  other_total: string
  month_total: string
}

export type YearlyOverviewData = {
  year: number
  months: MonthlyOverview[]
  year_total: string
}
