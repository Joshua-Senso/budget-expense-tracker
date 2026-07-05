export type RecurringExpense = {
  id: string
  user_id: string
  category_id: string
  description: string
  amount: string
  currency: string
  start_on: string
  frequency: string
  is_active: boolean
  end_on: string | null
  created_at: string
  updated_at: string
}

export type ProjectedExpense = {
  recurring_expense_id: string
  category_id: string
  description: string
  amount: string
  currency: string
  spent_on: string
  source: "generated"
}

export type RecurringCreatePayload = {
  category_id: string
  description: string
  amount: number
  currency: string
  start_on: string
  end_on?: string | null
}
