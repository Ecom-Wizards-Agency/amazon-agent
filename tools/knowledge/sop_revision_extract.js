/*
 * In-page BookStack revision-metadata extractor for tools/knowledge/sop_revision_check.mjs.
 *
 * Plain browser script, not a module: sop_revision_check.mjs reads this file as
 * text and evaluates it through CDP Runtime.evaluate (house pattern of
 * tools/knowledge/help_extract.js). The whole file is one expression. The Node
 * side may define a global-free option object by wrapping the expression:
 *
 *   (() => { const __SOP_REVISION_OPTIONS__ = { wantBody: true }; return <this file>; })()
 *
 * and gets back:
 *
 *   { url, title, isLogin, revisedIso, revisedSource, revisedText, revisionCount,
 *     bodyMarkdown, status, httpStatus, readyState, hasBody, hasPasswordField, error }
 *
 * status is one of ok | login-required | not-found | error. revisedIso comes
 * from the <time datetime> attribute of BookStack's "Updated <time> by <name>"
 * meta line, else its title attribute (revisedSource "datetime" | "title");
 * when neither parses, revisedText carries the relative text ("3 weeks ago")
 * and the Node side converts it against the check date (revisedSource
 * "relative"). The editor's name is never read into the result.
 * bodyMarkdown is filled only when the options ask for it.
 *
 * Read-only: it never clicks, types, mutates the DOM or reads cookies or
 * storage. Throw-safe: any error becomes { status: "error", error }.
 *
 * Outside a browser (no global document) it returns its pure helpers so the
 * extraction and the markdown converter can be tested on a fixture DOM.
 */
(() => {
  const SKIP_TAGS = new Set([
    "SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "SVG", "NAV", "HEADER", "FOOTER", "BUTTON", "FORM",
    "SELECT", "OPTION", "INPUT", "TEXTAREA", "IFRAME", "VIDEO", "AUDIO", "CANVAS", "LINK", "META", "HEAD", "TITLE",
  ]);
  const BLOCK_TAGS = new Set([
    "P", "DIV", "SECTION", "ARTICLE", "MAIN", "H1", "H2", "H3", "H4", "H5", "H6", "UL", "OL", "TABLE",
    "PRE", "BLOCKQUOTE", "DL", "DT", "DD", "FIGURE", "FIGCAPTION", "HR", "LI", "TR", "TBODY", "THEAD",
    "TFOOT", "DETAILS", "SUMMARY", "CENTER", "ADDRESS", "FIELDSET",
  ]);
  const MONTHS = [
    "january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december",
  ];
  const NOT_FOUND = /page not found|could not be found|\b404\b/i;

  const tagOf = (node) => String(node.tagName || node.nodeName || "").toUpperCase();
  const attr = (node, name) => (node && typeof node.getAttribute === "function" ? node.getAttribute(name) : null) || "";
  const kids = (node) => Array.from((node && node.childNodes) || []);
  const squash = (text) => String(text).replace(/\s+/g, " ");
  const hasClass = (node, name) => attr(node, "class").split(/\s+/).includes(name);
  const isBlock = (node) => node.nodeType === 1 && BLOCK_TAGS.has(tagOf(node));
  const isMeta = (node) => attr(node, "class").split(/\s+/).some((token) => /^entity-meta/.test(token));

  function textOf(node) {
    if (node.nodeType === 3) return node.nodeValue || "";
    if (node.nodeType !== 1 || SKIP_TAGS.has(tagOf(node))) return "";
    return kids(node).map(textOf).join("");
  }

  /** Depth-first element walk; visit(node, inMeta). Skips the page body when skipContent is set. */
  function walk(node, visit, { skipContent = false } = {}, inMeta = false) {
    if (!node || node.nodeType !== 1) return;
    if (skipContent && hasClass(node, "page-content")) return;
    const meta = inMeta || isMeta(node);
    visit(node, meta);
    for (const child of kids(node)) walk(child, visit, { skipContent }, meta);
  }

  function findFirst(root, predicate) {
    let found = null;
    const visit = (node) => {
      if (found || !node || node.nodeType !== 1) return;
      if (predicate(node)) { found = node; return; }
      for (const child of kids(node)) visit(child);
    };
    visit(root);
    return found;
  }

  // ---- dates

  const pad = (n) => String(n).padStart(2, "0");
  const monthOf = (word) => {
    const key = String(word || "").toLowerCase();
    return key.length >= 3 ? MONTHS.findIndex((name) => name.startsWith(key)) + 1 : 0;
  };
  const isoDay = (y, m, d) => {
    const probe = new Date(Date.UTC(y, m - 1, d));
    if (probe.getUTCFullYear() !== y || probe.getUTCMonth() !== m - 1 || probe.getUTCDate() !== d) return "";
    return `${y}-${pad(m)}-${pad(d)}`;
  };

  /**
   * Parse a datetime attribute or a BookStack title such as
   * "Mon, Mar 4, 2024 12:00 PM" or "2024-03-04 12:00:00".
   * Returns { iso, precision } with precision "exact" (an instant with a
   * timezone, iso in UTC "YYYY-MM-DDTHH:MM:SSZ") or "day" (iso "YYYY-MM-DD").
   */
  function parseAbsolute(raw) {
    const text = squash(raw || "").trim();
    if (!text) return null;
    let m = /^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.\d+)?)?\s*(Z|[+-]\d{2}:?\d{2})?)?$/i.exec(text);
    if (m) {
      const day = isoDay(Number(m[1]), Number(m[2]), Number(m[3]));
      if (!day) return null;
      if (m[4] !== undefined && m[7]) {
        const offset = m[7].toUpperCase() === "Z" ? "Z" : m[7].replace(/^([+-]\d{2})(\d{2})$/, "$1:$2");
        const ms = Date.parse(`${day}T${m[4]}:${m[5]}:${m[6] || "00"}${offset}`);
        if (Number.isFinite(ms)) return { iso: new Date(ms).toISOString().replace(/\.\d{3}Z$/, "Z"), precision: "exact" };
      }
      return { iso: day, precision: "day" };
    }
    // "Mon, Mar 4, 2024 12:00 PM", "March 4, 2024", "4 March 2024"
    m = /(?:^|[\s,])([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b/.exec(text);
    if (m && monthOf(m[1])) {
      const day = isoDay(Number(m[3]), monthOf(m[1]), Number(m[2]));
      return day ? { iso: day, precision: "day" } : null;
    }
    m = /(?:^|\s)(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})\b/.exec(text);
    if (m && monthOf(m[2])) {
      const day = isoDay(Number(m[3]), monthOf(m[2]), Number(m[1]));
      return day ? { iso: day, precision: "day" } : null;
    }
    return null;
  }

  // ---- BookStack meta

  /**
   * The smallest element outside the page body whose text starts with
   * "Updated". Lines inside BookStack's entity-meta block win; elsewhere the
   * line must hold a <time> or a titled element, so sidebar prose cannot match.
   */
  function findUpdatedLine(root) {
    const best = { meta: null, metaLength: Infinity, other: null, otherLength: Infinity };
    walk(root, (node, inMeta) => {
      if (SKIP_TAGS.has(tagOf(node))) return;
      const text = squash(textOf(node)).trim();
      if (!/^Updated\b/i.test(text) || text.length > 240) return;
      if (inMeta) {
        if (text.length <= best.metaLength) { best.meta = node; best.metaLength = text.length; }
        return;
      }
      const dated = findFirst(node, (el) => tagOf(el) === "TIME" || (el !== node && tagOf(el) !== "A" && attr(el, "title") !== ""));
      if (dated && text.length <= best.otherLength) { best.other = node; best.otherLength = text.length; }
    }, { skipContent: true });
    return best.meta || best.other;
  }

  /** Read the Updated line without its "by <name>" part. */
  function readUpdated(root) {
    const line = findUpdatedLine(root);
    if (!line) return { found: false, revisedIso: "", revisedSource: "", revisedText: "" };
    const timeEl = findFirst(line, (node) => tagOf(node) === "TIME")
      || findFirst(line, (node) => node !== line && tagOf(node) !== "A" && attr(node, "title") !== "");
    let revisedText = "";
    if (timeEl) revisedText = squash(textOf(timeEl)).trim();
    if (!revisedText) {
      const m = /^Updated\s+(.*?)(?:\s+by\b.*)?$/i.exec(squash(textOf(line)).trim());
      revisedText = m ? m[1].trim() : "";
    }
    for (const [source, value] of [["datetime", attr(timeEl, "datetime")], ["title", attr(timeEl, "title")]]) {
      const parsed = parseAbsolute(value);
      if (parsed) return { found: true, revisedIso: parsed.iso, revisedPrecision: parsed.precision, revisedSource: source, revisedText };
    }
    const parsedText = parseAbsolute(revisedText);
    if (parsedText) return { found: true, revisedIso: parsedText.iso, revisedPrecision: parsedText.precision, revisedSource: "text", revisedText };
    return { found: true, revisedIso: "", revisedPrecision: "", revisedSource: revisedText ? "relative" : "", revisedText };
  }

  /** "Revision #12" in the meta block, or a number inside the /revisions link. */
  function readRevisionCount(root) {
    let count = null;
    walk(root, (node) => {
      if (count !== null || SKIP_TAGS.has(tagOf(node))) return;
      const text = squash(textOf(node)).trim();
      if (text.length > 80) return;
      const isRevLink = tagOf(node) === "A" && /\/revisions\/?(?:$|[?#])/.test(attr(node, "href"));
      const m = /Revision\s*#\s*(\d+)/i.exec(text) || (isRevLink ? /(\d+)/.exec(text) : null);
      if (m) count = Number(m[1]);
    }, { skipContent: true });
    return count;
  }

  // ---- markdown (BookStack WYSIWYG content)

  function inline(node) {
    if (node.nodeType === 3) return squash(node.nodeValue || "");
    if (node.nodeType !== 1) return "";
    const tag = tagOf(node);
    if (tag === "IMG") {
      const src = attr(node, "src");
      return src ? `![${squash(attr(node, "alt")).trim()}](${src})` : "";
    }
    if (SKIP_TAGS.has(tag)) return "";
    if (tag === "BR") return "\n";
    const inner = kids(node).map(inline).join("");
    if ((tag === "STRONG" || tag === "B") && inner.trim()) return `**${inner.trim()}**`;
    if ((tag === "EM" || tag === "I") && inner.trim()) return `*${inner.trim()}*`;
    if (tag === "CODE" && inner.trim()) return `\`${inner.trim()}\``;
    if (tag === "A") {
      const href = attr(node, "href");
      const text = inner.trim();
      if (!href || href.startsWith("#") || /^javascript:/i.test(href)) return inner;
      if (!text) return "";
      return text === href ? `<${href}>` : `[${text}](${href})`;
    }
    return inner;
  }

  const cleanInline = (text) => text.split("\n").map((line) => line.replace(/ +/g, " ").trim()).filter(Boolean).join("\n");

  function listBlock(node, depth) {
    const ordered = tagOf(node) === "OL";
    const lines = [];
    let n = 0;
    for (const item of kids(node)) {
      if (item.nodeType !== 1) continue;
      if (tagOf(item) !== "LI") {
        if (tagOf(item) === "UL" || tagOf(item) === "OL") lines.push(listBlock(item, depth + 1));
        continue;
      }
      n += 1;
      const parts = [];
      const nested = [];
      for (const child of kids(item)) {
        const t = child.nodeType === 1 ? tagOf(child) : "";
        if (t === "UL" || t === "OL") { nested.push(listBlock(child, depth + 1)); continue; }
        if (child.nodeType === 1 && isBlock(child)) { parts.push(" ", blocks(child, []).join(" "), " "); continue; }
        parts.push(inline(child));
      }
      const text = cleanInline(parts.join("")).replace(/\n/g, " ");
      if (text) lines.push(`${"  ".repeat(depth)}${ordered ? `${n}.` : "-"} ${text}`);
      lines.push(...nested.filter(Boolean));
    }
    return lines.filter(Boolean).join("\n");
  }

  function tableBlock(node) {
    const rows = [];
    const collect = (el) => {
      for (const child of kids(el)) {
        if (child.nodeType !== 1) continue;
        const t = tagOf(child);
        if (t === "TR") rows.push(child);
        else if (t === "THEAD" || t === "TBODY" || t === "TFOOT") collect(child);
      }
    };
    collect(node);
    const out = [];
    rows.forEach((row, index) => {
      const cells = kids(row).filter((c) => c.nodeType === 1 && (tagOf(c) === "TD" || tagOf(c) === "TH"));
      if (!cells.length) return;
      const values = cells.map((cell) => cleanInline(blocks(cell, []).join(" ")).replace(/\n+/g, " ").replace(/\|/g, "\\|"));
      out.push(`| ${values.join(" | ")} |`);
      if (index === 0) out.push(`| ${cells.map(() => "---").join(" | ")} |`);
    });
    return out.join("\n");
  }

  function blocks(node, out) {
    let buffer = [];
    const flush = () => {
      const text = cleanInline(buffer.join(""));
      if (text) out.push(text);
      buffer = [];
    };
    for (const child of kids(node)) {
      if (child.nodeType === 3) { buffer.push(squash(child.nodeValue || "")); continue; }
      if (child.nodeType !== 1) continue;
      const tag = tagOf(child);
      if (SKIP_TAGS.has(tag)) continue;
      if (!isBlock(child)) { buffer.push(inline(child)); continue; }
      flush();
      const heading = /^H([1-6])$/.exec(tag);
      if (heading) {
        const text = cleanInline(inline(child)).replace(/\n/g, " ");
        if (text) out.push(`${"#".repeat(Number(heading[1]))} ${text}`);
      } else if (tag === "UL" || tag === "OL") {
        const list = listBlock(child, 0);
        if (list) out.push(list);
      } else if (tag === "TABLE") {
        const table = tableBlock(child);
        if (table) out.push(table);
      } else if (tag === "PRE") {
        const code = textOf(child).replace(/\s+$/, "");
        if (code.trim()) out.push("```\n" + code + "\n```");
      } else if (tag === "HR") {
        out.push("---");
      } else if (tag === "BLOCKQUOTE") {
        const inner = blocks(child, []);
        if (inner.length) out.push(inner.join("\n\n").split("\n").map((line) => `> ${line}`).join("\n"));
      } else if (tag === "P" || tag === "DT" || tag === "DD" || tag === "FIGCAPTION" || tag === "SUMMARY") {
        const text = cleanInline(inline(child));
        if (text) out.push(text);
      } else {
        blocks(child, out);
      }
    }
    flush();
    return out;
  }

  function toMarkdown(root) {
    return root ? blocks(root, []).join("\n\n").replace(/\n{3,}/g, "\n\n").trim() : "";
  }

  // ---- page

  function findBody(root) {
    return findFirst(root, (node) => hasClass(node, "page-content"))
      || findFirst(root, (node) => tagOf(node) === "MAIN" || tagOf(node) === "ARTICLE");
  }

  /**
   * Pure extraction over any DOM-like root (childNodes, nodeType, tagName,
   * getAttribute). context: { url, docTitle, wantBody, httpStatus, readyState }.
   */
  function extract(root, context = {}) {
    const url = String(context.url || "");
    let hasPasswordField = false;
    walk(root, (node) => {
      if (tagOf(node) === "INPUT" && attr(node, "type").toLowerCase() === "password") hasPasswordField = true;
    });
    const body = findBody(root);
    const pageContent = body && hasClass(body, "page-content") ? body : null;
    const h1 = (pageContent && findFirst(pageContent, (node) => tagOf(node) === "H1"))
      || findFirst(root, (node) => tagOf(node) === "H1" && !SKIP_TAGS.has(tagOf(node)));
    const docTitle = squash(context.docTitle || "").trim();
    const title = h1 ? squash(textOf(h1)).trim() : docTitle.replace(/\s+\|\s+[^|]*$/, "");
    const meta = readUpdated(root);
    const revisionCount = readRevisionCount(root);
    const notFound = Number(context.httpStatus) === 404 || NOT_FOUND.test(docTitle)
      || (!pageContent && NOT_FOUND.test(h1 ? textOf(h1) : ""));
    const isLogin = /\/login(?:[/?#]|$)/i.test(url) || hasPasswordField;
    let status = "ok";
    if (isLogin) status = "login-required";
    else if (notFound) status = "not-found";
    else if (!pageContent) status = "login-required";
    let bodyMarkdown = "";
    if (context.wantBody && status === "ok") {
      bodyMarkdown = toMarkdown(pageContent);
      const firstHeading = /^# ([^\n]+)\n*/.exec(bodyMarkdown);
      if (firstHeading && squash(firstHeading[1]).trim() === title) bodyMarkdown = bodyMarkdown.slice(firstHeading[0].length).trim();
    }
    return {
      url, title, isLogin: status === "login-required", revisedIso: meta.revisedIso || "",
      revisedPrecision: meta.revisedPrecision || "", revisedSource: meta.revisedSource || "",
      revisedText: meta.revisedText || "", revisionCount, bodyMarkdown, status,
      httpStatus: Number(context.httpStatus) || null, readyState: context.readyState || "",
      hasBody: Boolean(pageContent), hasPasswordField, updatedFound: meta.found, error: "",
    };
  }

  if (typeof document === "undefined") {
    return { extract, toMarkdown, parseAbsolute, readUpdated, readRevisionCount, findBody, textOf };
  }

  // ---- browser-only part
  try {
    const options = typeof __SOP_REVISION_OPTIONS__ === "object" && __SOP_REVISION_OPTIONS__ ? __SOP_REVISION_OPTIONS__ : {};
    let httpStatus = null;
    try {
      const nav = performance.getEntriesByType("navigation")[0];
      if (nav && nav.responseStatus) httpStatus = nav.responseStatus;
    } catch { /* keep null */ }
    return extract(document.documentElement, {
      url: location.href, docTitle: document.title, wantBody: Boolean(options.wantBody),
      httpStatus, readyState: document.readyState,
    });
  } catch (error) {
    let url = "";
    try { url = location.href; } catch { /* keep */ }
    return {
      url, title: "", isLogin: false, revisedIso: "", revisedPrecision: "", revisedSource: "", revisedText: "",
      revisionCount: null, bodyMarkdown: "", status: "error", httpStatus: null, readyState: "",
      hasBody: false, hasPasswordField: false, updatedFound: false, error: String((error && error.message) || error),
    };
  }
})()
