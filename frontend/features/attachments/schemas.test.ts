import { describe, expect, it } from "vitest"

import { MAX_RECEIPT_SIZE_BYTES, isAllowedReceiptType, isReceiptSizeValid } from "./schemas"

function makeFile(type: string, sizeBytes: number) {
  return new File([new Uint8Array(Math.max(sizeBytes, 0))], "receipt", { type })
}

describe("isAllowedReceiptType", () => {
  it.each(["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"])(
    "accepts %s",
    (type) => {
      expect(isAllowedReceiptType(makeFile(type, 1024))).toBe(true)
    },
  )

  it.each(["application/pdf", "image/gif", ""])("rejects %s", (type) => {
    expect(isAllowedReceiptType(makeFile(type, 1024))).toBe(false)
  })
})

describe("isReceiptSizeValid", () => {
  it("accepts a file at the size limit", () => {
    expect(isReceiptSizeValid(makeFile("image/jpeg", MAX_RECEIPT_SIZE_BYTES))).toBe(true)
  })

  it("rejects a file over the size limit", () => {
    expect(isReceiptSizeValid(makeFile("image/jpeg", MAX_RECEIPT_SIZE_BYTES + 1))).toBe(false)
  })

  it("rejects an empty file", () => {
    expect(isReceiptSizeValid(makeFile("image/jpeg", 0))).toBe(false)
  })
})
