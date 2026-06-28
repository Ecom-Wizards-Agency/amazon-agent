#!/usr/bin/env node
import fs from "node:fs"
import path from "node:path"

function slugify(value) {
  return String(value || "opportunity-explorer-export")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80)
}

function clean(value) {
  return String(value || "").replace(/\s+/g, " ").trim()
}

function tableToMarkdown(table) {
  const rows = (table.rows || []).filter((row) => row.some(Boolean))
  if (!rows.length) return ""

  const width = Math.max(...rows.map((row) => row.length))
  const normalized = rows.map((row) =>
    Array.from({ length: width }, (_, index) => clean(row[index]))
  )
  const header = normalized[0]
  const separator = Array.from({ length: width }, () => "---")
  const body = normalized.slice(1)

  return [header, separator, ...body]
    .map((row) => `| ${row.join(" | ")} |`)
    .join("\n")
}

function toMarkdown(data) {
  const title = clean(data.nicheTitle || data.pageTitle || "Opportunity Explorer Export")
  const lines = [
    `# ${title}`,
    "",
    `- Exported: ${data.exportedAt || ""}`,
    `- URL: ${data.url || ""}`,
    `- Schema: ${data.schemaVersion || ""}`,
    "",
  ]

  if (Array.isArray(data.sections) && data.sections.length) {
    lines.push("## Detected Sections", "")
    for (const section of data.sections) {
      lines.push(`### ${clean(section.title)}`, "")
      lines.push(clean(section.snippet), "")
    }
  }

  if (Array.isArray(data.dataPoints) && data.dataPoints.length) {
    lines.push("## Data Points", "")
    for (const point of data.dataPoints.slice(0, 80)) {
      lines.push(`- ${clean(point)}`)
    }
    lines.push("")
  }

  if (Array.isArray(data.tables) && data.tables.length) {
    lines.push("## Tables", "")
    for (const table of data.tables) {
      const markdown = tableToMarkdown(table)
      if (!markdown) continue
      lines.push(`### Table ${Number(table.index || 0) + 1}`, "")
      lines.push(markdown, "")
    }
  }

  if (data.tabs && typeof data.tabs === "object") {
    lines.push("## Tabs", "")
    for (const [name, tab] of Object.entries(data.tabs)) {
      lines.push(`### ${name}`, "")
      if (tab.error) {
        lines.push(`Error: ${tab.error}`, "")
        continue
      }
      if (Array.isArray(tab.sections) && tab.sections.length) {
        for (const section of tab.sections) {
          lines.push(`#### ${clean(section.title)}`, "")
          lines.push(clean(section.snippet), "")
        }
      } else if (tab.text) {
        lines.push(clean(tab.text).slice(0, 6000), "")
      }
    }
  }

  return `${lines.join("\n").trim()}\n`
}

const inputPath = process.argv[2]

if (!inputPath) {
  console.error("Usage: node tools/opportunity-explorer/format-opportunity-explorer-export.mjs <input.json> [output-dir]")
  process.exit(1)
}

const data = JSON.parse(fs.readFileSync(inputPath, "utf8"))
const date = new Date().toISOString().slice(0, 10)
const outputDir = process.argv[3] || path.join("output", "unknown", "opportunity-data")
fs.mkdirSync(outputDir, { recursive: true })

const slug = slugify(data.nicheTitle || data.pageTitle || path.basename(inputPath, ".json"))
const jsonPath = path.join(outputDir, `${date}_${slug}.json`)
const markdownPath = path.join(outputDir, `${date}_${slug}.md`)

fs.writeFileSync(jsonPath, `${JSON.stringify(data, null, 2)}\n`)
fs.writeFileSync(markdownPath, toMarkdown(data))

console.log(JSON.stringify({ jsonPath, markdownPath }, null, 2))
