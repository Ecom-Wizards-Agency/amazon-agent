/*
 * DEPRECATED (2026-07-05): DOM-scraping fallback only — use fetch-poe.js +
 * run-poe.mjs instead (POE's internal GraphQL API returns every tab in one
 * call; see references/poe-endpoints.md). Kept until the fetch path has
 * survived a few real client runs, then delete.
 *
 * Browser-side Product Opportunity Explorer extractor.
 *
 * Usage:
 * 1. Open the relevant Amazon Seller Central Product Opportunity Explorer page.
 * 2. Run this script in the page context.
 * 3. Call: await window.amazonAgentExtractOpportunityExplorer()
 *
 * The function returns JSON-friendly data. It does not inspect cookies,
 * storage, credentials, or hidden session data.
 */

(function () {
  function cleanText(value) {
    return String(value || "")
      .replace(/\s+/g, " ")
      .trim()
  }

  function unique(values) {
    return Array.from(new Set(values.map(cleanText).filter(Boolean)))
  }

  function textHash(value) {
    let hash = 0
    const text = String(value || "")
    for (let i = 0; i < text.length; i += 1) {
      hash = (hash << 5) - hash + text.charCodeAt(i)
      hash |= 0
    }
    return String(hash)
  }

  function getPageTitle() {
    const selectors = [
      'h1[data-testid*="niche" i]',
      '[class*="nicheTitle" i]',
      "h1",
      "h2",
    ]

    for (const selector of selectors) {
      const element = document.querySelector(selector)
      const text = cleanText(element && element.textContent)
      if (text) return text
    }

    return cleanText(document.title)
  }

  function extractTables(root) {
    return Array.from(root.querySelectorAll("table"))
      .map((table, index) => {
        const rows = Array.from(table.querySelectorAll("tr")).map((row) =>
          Array.from(row.querySelectorAll("th,td")).map((cell) =>
            cleanText(cell.textContent)
          )
        )

        return {
          index,
          rows: rows.filter((row) => row.some(Boolean)),
        }
      })
      .filter((table) => table.rows.length)
  }

  function extractDataPoints(root) {
    const candidates = Array.from(
      root.querySelectorAll(
        [
          '[class*="metric" i]',
          '[class*="stat" i]',
          '[class*="summary" i]',
          '[class*="insight" i]',
          '[data-testid*="metric" i]',
          '[data-testid*="summary" i]',
          "kat-card",
          "kat-label",
        ].join(",")
      )
    )

    return unique(
      candidates
        .map((element) => cleanText(element.innerText || element.textContent))
        .filter((text) => text.length > 8 && text.length < 500)
    ).slice(0, 200)
  }

  function findTabButtons() {
    const expectedNames = [
      "Insights & Trends",
      "Products",
      "Search Terms",
      "Customer Review Insights",
      "Returns",
    ]

    const clickable = Array.from(
      document.querySelectorAll(
        [
          '[role="tab"]',
          "button",
          "a",
          "kat-tab",
          "kat-tab-header",
          '[class*="tab" i]',
          '[class*="segment" i]',
        ].join(",")
      )
    )

    const tabs = []
    for (const expectedName of expectedNames) {
      const match = clickable.find((element) => {
        const text = cleanText(element.innerText || element.textContent)
        return (
          text.toLowerCase() === expectedName.toLowerCase() ||
          (text.toLowerCase().includes(expectedName.toLowerCase()) &&
            text.length <= expectedName.length + 30)
        )
      })

      if (match && !tabs.some((tab) => tab.element === match)) {
        tabs.push({ name: expectedName, element: match })
      }
    }

    return tabs
  }

  function getMainContentText() {
    const selectors = [
      "main",
      '[role="main"]',
      '[class*="content" i]',
      '[class*="page" i]',
      "body",
    ]

    for (const selector of selectors) {
      const element = document.querySelector(selector)
      const text = cleanText(element && element.innerText)
      if (text.length > 200) return text
    }

    return cleanText(document.body && document.body.innerText)
  }

  function extractSectionSnippets(text) {
    const sectionNames = [
      "Niche Overview",
      "Top Product Features",
      "Customer Reviews",
      "Customer Review Insights",
      "Returns",
      "Search Terms",
      "Pricing",
      "Seasonal Patterns",
      "Brand Structure",
      "Success Factors",
      "Evolution Indicators",
      "Niche Dynamics",
      "Demographics",
    ]

    const sections = []
    for (const name of sectionNames) {
      const index = text.toLowerCase().indexOf(name.toLowerCase())
      if (index === -1) continue

      sections.push({
        title: name,
        snippet: cleanText(text.slice(index, index + 2500)),
      })
    }

    return sections
  }

  async function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }

  async function clickAndExtractTabs() {
    const tabs = findTabButtons()
    const results = {}
    const seen = new Set()

    for (const tab of tabs) {
      try {
        tab.element.scrollIntoView({ block: "center", inline: "nearest" })
        tab.element.click()
        await sleep(1500)

        const text = getMainContentText()
        const hash = textHash(text.slice(0, 2000))
        if (!seen.has(hash) || text.length > 0) {
          seen.add(hash)
          results[tab.name] = {
            text,
            tables: extractTables(document),
            dataPoints: extractDataPoints(document),
            sections: extractSectionSnippets(text),
          }
        }
      } catch (error) {
        results[tab.name] = {
          error: error && error.message ? error.message : String(error),
        }
      }
    }

    return results
  }

  async function extractOpportunityExplorer() {
    const rawText = getMainContentText()

    return {
      schemaVersion: "amazon-agent.oei-export.v1",
      exportedAt: new Date().toISOString(),
      url: window.location.href,
      pageTitle: cleanText(document.title),
      nicheTitle: getPageTitle(),
      sections: extractSectionSnippets(rawText),
      tables: extractTables(document),
      dataPoints: extractDataPoints(document),
      tabs: await clickAndExtractTabs(),
      rawText,
    }
  }

  window.amazonAgentExtractOpportunityExplorer = extractOpportunityExplorer
})()
