"use client"

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

import { SUPPORTED_CURRENCIES } from "../constants"

interface CurrencySelectProps {
  value: string
  onValueChange: (value: string) => void
}

function CurrencySelect({ value, onValueChange }: CurrencySelectProps) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {SUPPORTED_CURRENCIES.map((code) => (
          <SelectItem key={code} value={code}>
            {code}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

export { CurrencySelect }
