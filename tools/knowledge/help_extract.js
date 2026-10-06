/*
 * In-page Amazon help article extractor for tools/knowledge/help_capture.mjs.
 *
 * Plain browser script, not a module: help_capture.mjs reads this file as text
 * and evaluates it through CDP Runtime.evaluate (house pattern of
 * tools/opportunity-explorer/fetch-poe.js). The whole file is one expression
 * that returns:
 *
 *   { url, title, isLogin, accountLabel, wordCount, bodyMarkdown, status,
 *     loading, notFound, hasSignInForm, container, articleFound, workspace }
 *
 * Seller Central renders each help article inside the Seller Assistant
 * workspace: H1 "Actions", H1 "Seller Assistant", then the article H1, and the
 * article arrives seconds after the workspace. findArticle() takes the first
 * non-workspace H1 as the title, uses a known article container or the nearest
 * ancestor of that H1 holding real text, and skips the workspace roots. While
 * only the workspace has rendered, status is "shell" and articleFound is false.
 *
 * status is one of ok | shell | missing | login-required. The Node side owns
 * the minimum-word wait, the redirect check and every scrub; accountLabel is
 * returned only so the Node side can replace it with the placeholder.
 *
 * Read-only: it never clicks, types, mutates the DOM or reads cookies or
 * storage. Navigation, headers, footers, language lists and breadcrumbs are
 * skipped while walking instead of being removed from the live page.
 *
 * Outside a browser (no global document) it returns its pure helpers so the
 * markdown converter can be tested on a fixture DOM.
 */
(() => {
  const SKIP_TAGS = new Set([
    "SCRIPT", "STYLE", "NOSCRIPT", "TEMPLATE", "SVG", "NAV", "HEADER", "FOOTER",
    "ASIDE", "BUTTON", "FORM", "SELECT", "OPTION", "INPUT", "TEXTAREA", "IFRAME",
    "IMG", "PICTURE", "VIDEO", "AUDIO", "CANVAS", "LINK", "META", "HEAD", "TITLE",
  ]);
  const SKIP_ROLES = new Set([
    "navigation", "banner", "contentinfo", "search", "menu", "menubar", "toolbar", "dialog", "alertdialog",
  ]);
  // Matched against each class token and the id as whole dash/underscore segments,
  // so an article section id such as "feedback-manager" is kept.
  const NOISE_TOKEN = /(?:^|[-_])(?:breadcrumbs?|(?:lang|language|locale)[-_]?(?:switch|switcher|picker|select|selector|list|menu)|navbar|(?:site|global)[-_]?(?:header|footer)|skip[-_]?link|cookie[-_]?(?:banner|consent|notice)|sidebar|(?:side|left|help)[-_]?nav|nav[-_]?menu|(?:account|partner)[-_]?switcher)(?:$|[-_])/i;
  const NOISE_LABEL = /breadcrumb|language|locale|navigation/i;
  const LANGUAGE_NAMES = new Set([
    "English", "Deutsch", "Español", "Français", "Italiano", "日本語", "한국어", "ไทย",
    "Tiếng Việt", "हिंदी", "தமிழ்", "Português", "中文(简体)", "中文(繁體)", "Nederlands",
    "Polski", "Svenska", "Türkçe", "العربية", "Čeština",
  ]);
  const BLOCK_TAGS = new Set([
    "P", "DIV", "SECTION", "ARTICLE", "MAIN", "H1", "H2", "H3", "H4", "H5", "H6", "UL", "OL",
    "TABLE", "PRE", "BLOCKQUOTE", "DL", "DT", "DD", "FIGURE", "FIGCAPTION", "HR", "LI", "TR",
    "TBODY", "THEAD", "TFOOT", "DETAILS", "SUMMARY", "CENTER", "ADDRESS", "FIELDSET",
  ]);

  const tagOf = (node) => String(node.tagName || node.nodeName || "").toUpperCase();
  const attr = (node, name) => (typeof node.getAttribute === "function" ? node.getAttribute(name) : null) || "";
  const kids = (node) => {
    const light = Array.from(node.childNodes || []);
    if (!light.length && node.shadowRoot) return Array.from(node.shadowRoot.childNodes || []);
    return light;
  };
  const isBlock = (node) => node.nodeType === 1 && (BLOCK_TAGS.has(tagOf(node)) || tagOf(node).includes("-"));
  const squash = (text) => String(text).replace(/\s+/g, " ");

  function textOf(node) {
    if (node.nodeType === 3) return node.nodeValue || "";
    if (node.nodeType !== 1 || SKIP_TAGS.has(tagOf(node))) return "";
    return kids(node).map(textOf).join(" ");
  }

  function isLanguageList(node) {
    const items = kids(node).filter((child) => child.nodeType === 1);
    if (items.length < 3) return false;
    const hits = items.filter((child) => LANGUAGE_NAMES.has(squash(textOf(child)).trim())).length;
    return hits >= 3 && hits / items.length >= 0.6;
  }

  // Elements excluded for the current conversion (the Seller Assistant workspace roots).
  let extraSkip = new Set();

  function isNoise(node) {
    if (node.nodeType !== 1) return false;
    if (extraSkip.has(node)) return true;
    const tag = tagOf(node);
    if (SKIP_TAGS.has(tag)) return true;
    if (typeof node.hasAttribute === "function" && node.hasAttribute("hidden")) return true;
    if (attr(node, "aria-hidden") === "true") return true;
    if (SKIP_ROLES.has(attr(node, "role").toLowerCase())) return true;
    const tokens = `${attr(node, "class")} ${attr(node, "id")}`.split(/\s+/).filter(Boolean);
    if (tokens.some((token) => NOISE_TOKEN.test(token))) return true;
    if (NOISE_LABEL.test(attr(node, "aria-label"))) return true;
    if ((tag === "UL" || tag === "OL" || tag === "DIV") && isLanguageList(node)) return true;
    return false;
  }

  function inline(node) {
    if (node.nodeType === 3) return squash(node.nodeValue || "");
    if (node.nodeType !== 1 || isNoise(node)) return "";
    const tag = tagOf(node);
    if (tag === "BR") return "\n";
    const inner = kids(node).map(inline).join("");
    if ((tag === "STRONG" || tag === "B") && inner.trim()) return `**${inner.trim()}**`;
    if (tag === "CODE" && inner.trim()) return `\`${inner.trim()}\``;
    return inner;
  }

  const cleanInline = (text) => text.split("\n").map((line) => line.replace(/ +/g, " ").trim()).filter(Boolean).join("\n");

  function listBlock(node, depth) {
    const ordered = tagOf(node) === "OL";
    const lines = [];
    let n = 0;
    for (const item of kids(node)) {
      if (item.nodeType !== 1 || isNoise(item)) continue;
      if (tagOf(item) !== "LI") {
        if (tagOf(item) === "UL" || tagOf(item) === "OL") lines.push(listBlock(item, depth + 1));
        continue;
      }
      n += 1;
      const textParts = [];
      const nested = [];
      for (const child of kids(item)) {
        const t = child.nodeType === 1 ? tagOf(child) : "";
        if (t === "UL" || t === "OL") { if (!isNoise(child)) nested.push(listBlock(child, depth + 1)); continue; }
        if (child.nodeType === 1 && isBlock(child)) { textParts.push(" ", blocksToText(child).replace(/\n+/g, " "), " "); continue; }
        textParts.push(inline(child));
      }
      const text = cleanInline(textParts.join("")).replace(/\n/g, " ");
      const prefix = `${"  ".repeat(depth)}${ordered ? `${n}.` : "-"} `;
      if (text) lines.push(prefix + text);
      lines.push(...nested.filter(Boolean));
    }
    return lines.filter(Boolean).join("\n");
  }

  function tableBlock(node) {
    const rows = [];
    const collect = (el) => {
      for (const child of kids(el)) {
        if (child.nodeType !== 1 || isNoise(child)) continue;
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
      const values = cells.map((cell) => cleanInline(blocksToText(cell)).replace(/\n+/g, " ").replace(/\|/g, "\\|"));
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
      if (child.nodeType !== 1 || isNoise(child)) continue;
      if (!isBlock(child)) { buffer.push(inline(child)); continue; }
      flush();
      const tag = tagOf(child);
      const heading = /^H([1-6])$/.exec(tag);
      if (heading) {
        const text = cleanInline(inline(child)).replace(/\n/g, " ").replace(/^\*\*(.*)\*\*$/, "$1");
        if (text) out.push(`${"#".repeat(Math.min(Number(heading[1]), 4))} ${text}`);
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
        continue;
      } else if (tag === "P" || tag === "DT" || tag === "DD" || tag === "FIGCAPTION" || tag === "SUMMARY") {
        const text = cleanInline(inline(child));
        if (text) out.push(text);
      } else if (tag === "BLOCKQUOTE") {
        const inner = [];
        blocks(child, inner);
        if (inner.length) out.push(inner.join("\n\n").split("\n").map((line) => `> ${line}`).join("\n"));
      } else {
        blocks(child, out);
      }
    }
    flush();
    return out;
  }

  function blocksToText(node) {
    return blocks(node, []).join("\n\n");
  }

  // Exact blocks of the Seller Assistant / Actions workspace that Seller Central
  // renders around every help article. A safety net behind the chrome-root skip.
  const CHROME_BLOCKS = new Set([
    "# Actions", "# Seller Assistant", "New chat", "Sorry! There's a network error. Try again later.",
    "## No actions required",
    "There are no actions in this workspace. However, you can use the filter above to check for other actions.",
    "#### Explore with a canvas (Beta)", "Seller Assistant can turn your data into smart business decisions with a canvas.",
    "#### Where to start", "#### Recently edited",
  ]);
  const CHROME_H1 = /^(?:actions|seller assistant)$/i;

  function toMarkdown(root, { skip = null } = {}) {
    const previous = extraSkip;
    extraSkip = skip || new Set();
    try {
      return blocks(root, []).filter((block) => !CHROME_BLOCKS.has(block.trim()))
        .join("\n\n").replace(/\n{3,}/g, "\n\n").trim();
    } finally {
      extraSkip = previous;
    }
  }

  // Depth-first walk over elements with their ancestor chain (root first).
  function walkElements(root, visit, ancestors = []) {
    for (const child of kids(root)) {
      if (child.nodeType !== 1) continue;
      if (visit(child, ancestors) === false) continue;
      walkElements(child, visit, [...ancestors, child]);
    }
  }

  const KNOWN_IDS = new Set(["help-content", "help-article", "article-body"]);
  const KNOWN_CLASSES = new Set([
    "help-content", "help-article", "help-article-content", "help-page-content", "hh-content", "article-content", "article-body",
  ]);
  const isKnownContainer = (node) => KNOWN_IDS.has(attr(node, "id"))
    || attr(node, "class").split(/\s+/).some((token) => KNOWN_CLASSES.has(token));

  /**
   * Locate the help article on a page that may wrap it in the Seller Assistant
   * workspace (H1s "Actions" and "Seller Assistant" before the article H1).
   * Returns { container, selector, title, articleH1, chromeRoots, workspace }.
   * container is null while only the workspace chrome has rendered.
   */
  function findArticle(root) {
    const h1s = [];
    const known = [];
    walkElements(root, (node, ancestors) => {
      if (SKIP_TAGS.has(tagOf(node)) && tagOf(node) !== "HEADER") return false;
      if (tagOf(node) === "H1") h1s.push({ node, ancestors, text: squash(textOf(node)).trim() });
      if (isKnownContainer(node)) known.push({ node, ancestors });
      return true;
    });
    const chrome = h1s.filter((h) => CHROME_H1.test(h.text));
    const article = h1s.find((h) => h.text && !CHROME_H1.test(h.text) && !h.ancestors.some((a) => tagOf(a) !== "HEADER" && isNoise(a))) || null;
    const workspace = chrome.length > 0;
    // Chrome roots: for each chrome H1, the highest ancestor that holds neither the
    // article H1 nor a known article container.
    const protectedNodes = new Set();
    if (article) { protectedNodes.add(article.node); article.ancestors.forEach((a) => protectedNodes.add(a)); }
    for (const k of known) { protectedNodes.add(k.node); k.ancestors.forEach((a) => protectedNodes.add(a)); }
    const chromeRoots = new Set();
    for (const h of chrome) {
      let top = h.node;
      for (let i = h.ancestors.length - 1; i >= 0; i -= 1) {
        if (protectedNodes.has(h.ancestors[i])) break;
        top = h.ancestors[i];
      }
      if (!protectedNodes.has(top)) chromeRoots.add(top);
    }
    const wordsOf = (node) => countWords(toMarkdown(node, { skip: chromeRoots }));
    let container = null;
    let selector = "";
    for (const k of known) {
      if (chromeRoots.has(k.node) || k.ancestors.some((a) => chromeRoots.has(a))) continue;
      if (wordsOf(k.node) >= 20) { container = k.node; selector = "known-container"; break; }
    }
    if (!container && article) {
      const h1Words = countWords(article.text);
      for (let i = article.ancestors.length - 1; i >= 0; i -= 1) {
        const candidate = article.ancestors[i];
        if (candidate === root) break;
        if (wordsOf(candidate) - h1Words >= 20) { container = candidate; selector = "article-h1-ancestor"; break; }
      }
    }
    return { container, selector, title: article ? article.text : "", articleH1: article ? article.node : null, chromeRoots, workspace };
  }

  function countWords(markdown) {
    return String(markdown).split(/\s+/).filter((token) => /[\p{L}\p{N}]/u.test(token)).length;
  }

  function hasLoadingLine(markdown) {
    return /(^|\n)[ \t]*Loading(?:\.{0,3}|…)?[ \t]*(\n|$)/.test(markdown);
  }

  if (typeof document === "undefined") {
    return { toMarkdown, countWords, hasLoadingLine, isNoise, textOf, findArticle, LANGUAGE_NAMES };
  }

  // ---- browser-only part ----
  const SELECTORS = [
    "#help-content", ".help-content", "[data-testid=\"help-content\"]", "[data-test-id=\"help-content\"]",
    ".help-article", "#help-article", ".help-article-content", ".help-page-content", ".hh-content",
    ".article-content", ".article-body", "#article-body",
    "#AACApplicationBody article", "#AACApplicationBody main",
    "article", "main", "[role=\"main\"]", "#AACApplicationBody",
  ];

  function wordsIn(el) {
    return countWords(textOf(el));
  }

  function largestTextBlock() {
    const candidates = Array.from(document.querySelectorAll("article, main, section, div")).slice(0, 4000);
    let best = null;
    let bestScore = 0;
    const scores = new Map();
    for (const el of candidates) {
      if (isNoise(el)) continue;
      const parts = el.querySelectorAll("p, li, td, h1, h2, h3, h4");
      if (parts.length < 3) continue;
      let score = 0;
      for (const part of parts) score += (part.textContent || "").length;
      for (const link of el.querySelectorAll("a")) score -= (link.textContent || "").length * 0.5;
      scores.set(el, score);
      if (score > bestScore) { best = el; bestScore = score; }
    }
    if (!best) return null;
    // Prefer the deepest element that still holds most of the best text.
    let chosen = best;
    for (const [el, score] of scores) {
      if (score >= bestScore * 0.8 && chosen.contains(el) && el !== chosen) chosen = el;
    }
    return chosen;
  }

  function findContainer() {
    for (const selector of SELECTORS) {
      let el = null;
      try { el = document.querySelector(selector); } catch { el = null; }
      if (el && wordsIn(el) >= 20) return { el, selector };
    }
    const block = largestTextBlock();
    return block ? { el: block, selector: "largest-text-block" } : { el: null, selector: "" };
  }

  function readAccountLabel() {
    const direct = [
      "[data-test-id=\"partner-switcher-account-name\"]",
      ".dropdown-account-switcher-header-label-global",
      ".partner-dropdown-button .partner-label",
      "#partner-switcher .partner-label",
      ".sc-account-switcher-name",
    ];
    for (const selector of direct) {
      let el = null;
      try { el = document.querySelector(selector); } catch { el = null; }
      const text = el ? squash(el.textContent || "").trim() : "";
      if (text) return text;
    }
    // Ads console header: a button holding the account name paragraph and a
    // second paragraph such as "Sponsored ads, United States".
    for (const button of document.querySelectorAll("button")) {
      const paras = Array.from(button.querySelectorAll("p"));
      if (paras.length < 2) continue;
      const second = squash(paras[1].textContent || "").trim();
      if (/sponsored ads|amazon dsp|multiple countries|united states|advertis/i.test(second)) {
        const first = squash(paras[0].textContent || "").trim();
        if (first) return first;
      }
    }
    return "";
  }

  const url = location.href;
  const hasSignInForm = !!document.querySelector(
    "form[name=\"signIn\"], #ap_email, #ap_password, #signInSubmit, input[type=\"password\"]",
  );
  const found = findArticle(document.body || document.documentElement);
  let el = found.container;
  let selector = found.selector;
  // Pages without the Seller Assistant workspace (Ads Support, Ads docs) keep the
  // selector and largest-text fallbacks. Workspace pages never fall back: the
  // largest block there is the workspace itself, so they wait for the article.
  if (!el && !found.workspace) ({ el, selector } = findContainer());
  const articleFound = !!el;
  const isLogin = /\/ap\//.test(url) || (hasSignInForm && (!el || selector === "largest-text-block"));
  const bodyMarkdown = el ? toMarkdown(el, { skip: found.chromeRoots }) : "";
  const wordCount = countWords(bodyMarkdown);
  let loading = hasLoadingLine(bodyMarkdown) || document.readyState !== "complete";
  if (!loading && el) {
    try { loading = !!el.querySelector("[aria-busy=\"true\"], kat-spinner, .kat-spinner, .loading-spinner"); } catch { /* keep */ }
  }
  let title = found.title;
  if (!title && el && !found.workspace) {
    const h1 = el.querySelector("h1") || document.querySelector("h1");
    title = h1 ? squash(textOf(h1)).trim() : "";
  }
  if (!title && !found.workspace) title = squash(document.title || "").trim();
  // Only the document title, or a near-empty body, may declare the page gone:
  // short real articles can mention retired features in their text.
  const NOT_FOUND = /page not found|page you requested|we couldn['’]t find|\b404\b/i;
  const notFound = NOT_FOUND.test(document.title || "") || (wordCount < 25 && NOT_FOUND.test(bodyMarkdown));
  let status = "ok";
  if (isLogin) status = "login-required";
  else if (notFound) status = "missing";
  else if (loading || wordCount === 0 || !articleFound) status = "shell";
  return {
    url, title, isLogin, accountLabel: readAccountLabel(), wordCount, bodyMarkdown, status,
    loading, notFound, hasSignInForm, container: selector, articleFound, workspace: found.workspace,
  };
})()
