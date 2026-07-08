import "@testing-library/jest-dom/vitest"

// jsdom doesn't implement scrollIntoView; Radix's <Select> calls it when its
// dropdown opens, which throws in any test that actually opens one.
Element.prototype.scrollIntoView = Element.prototype.scrollIntoView ?? (() => {})
