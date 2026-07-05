import { describe, expect, it } from "vitest"

import {
  MAX_RECEIPT_SIZE_BYTES,
  isAllowedReceiptType,
  isReceiptSizeValid,
  resolveReceiptContentType,
} from "./schemas"

function makeFile(type: string, sizeBytes: number, filename = "receipt") {
  return new File([new Uint8Array(Math.max(sizeBytes, 0))], filename, { type })
}

describe("isAllowedReceiptType", () => {
  it.each(["image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"])(
    "accepts %s",
    (type) => {
      expect(isAllowedReceiptType(makeFile(type, 1024))).toBe(true)
    },
  )

  it.each(["application/pdf", "image/gif"])("rejects %s", (type) => {
    expect(isAllowedReceiptType(makeFile(type, 1024))).toBe(false)
  })

  it("rejects an empty type with no recognizable extension", () => {
    expect(isAllowedReceiptType(makeFile("", 1024, "receipt"))).toBe(false)
  })

  it("rejects an empty type with an unsupported extension", () => {
    expect(isAllowedReceiptType(makeFile("", 1024, "receipt.pdf"))).toBe(false)
  })
})

describe("resolveReceiptContentType", () => {
  it.each([
    ["receipt.heic", "image/heic"],
    ["receipt.HEIC", "image/heic"],
    ["receipt.heif", "image/heif"],
    ["receipt.jpg", "image/jpeg"],
    ["receipt.jpeg", "image/jpeg"],
    ["receipt.png", "image/png"],
    ["receipt.webp", "image/webp"],
  ])(
    "falls back to the extension when the browser reports no MIME type for %s",
    (filename, expected) => {
      expect(resolveReceiptContentType(makeFile("", 1024, filename))).toBe(expected)
    },
  )

  it("prefers the reported MIME type over the extension when both are present", () => {
    expect(resolveReceiptContentType(makeFile("image/png", 1024, "receipt.jpg"))).toBe(
      "image/png",
    )
  })

  it("returns null for a disallowed MIME type regardless of extension", () => {
    expect(resolveReceiptContentType(makeFile("application/pdf", 1024, "receipt.png"))).toBeNull()
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
