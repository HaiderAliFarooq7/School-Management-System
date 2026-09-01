import { apiClient } from './client'

export interface Expense {
  expense_id: number
  expense_date: string
  category: string
  description: string
  paid_to: string
  for_month: string | null
  amount: number
  payment_method: string
  note: string | null
  recorded_by_username: string
}

export interface ExpensePayload {
  expense_date: string
  category: string
  description?: string
  paid_to?: string
  for_month?: string | null
  amount: number
  payment_method?: string
  note?: string | null
}

export interface CategoryTotal {
  category: string
  total: number
  count: number
}

export interface ExpenseSummary {
  income: number
  expenses: number
  net: number
  salary_total: number
  by_category: CategoryTotal[]
  monthly: { month: string; income: number; expenses: number; net: number }[]
}

export const PAYMENT_METHODS = ['Cash', 'Bank Transfer', 'Cheque', 'Online']

export async function listExpenseCategories(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>('/expenses/categories')
  return data
}

export async function listExpenses(params: {
  date_from?: string
  date_to?: string
  category?: string
}): Promise<Expense[]> {
  const { data } = await apiClient.get<Expense[]>('/expenses', {
    params: {
      date_from: params.date_from ?? '',
      date_to: params.date_to ?? '',
      category: params.category ?? '',
    },
  })
  return data
}

export async function createExpense(payload: ExpensePayload): Promise<Expense> {
  const { data } = await apiClient.post<Expense>('/expenses', payload)
  return data
}

export async function updateExpense(expenseId: number, payload: ExpensePayload): Promise<Expense> {
  const { data } = await apiClient.put<Expense>(`/expenses/${expenseId}`, payload)
  return data
}

export async function deleteExpense(expenseId: number): Promise<void> {
  await apiClient.delete(`/expenses/${expenseId}`)
}

export async function getExpenseSummary(params: {
  date_from?: string
  date_to?: string
}): Promise<ExpenseSummary> {
  const { data } = await apiClient.get<ExpenseSummary>('/expenses/summary', {
    params: { date_from: params.date_from ?? '', date_to: params.date_to ?? '' },
  })
  return data
}
