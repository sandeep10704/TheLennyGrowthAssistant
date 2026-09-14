# Secure Rendering Architecture & Threat Defense Specification

This document provides a comprehensive security review and architectural guide for safely rendering AI-generated artifacts in the **Lenny Growth Assistant**.

---

## 1. Threat Model & Attack Vectors

When LLMs generate dynamic HTML/CSS, the output must be treated as **untrusted user input**. Without strict isolation, rendering arbitrary markup exposes the host application to:

1. **Stored / DOM-based Cross-Site Scripting (XSS)**:
   - Injection of malicious `<script>` tags, `<img onerror=...>`, or `javascript:` pseudo-protocols.
   - Attackers could steal user session tokens, JWTs, Supabase database credentials, or conversational history from `localStorage` / `sessionStorage` / cookies.
2. **Parent DOM Hijacking & Session Impersonation**:
   - Accessing `window.parent` or `window.top` to rewrite the application UI, forge chat messages, or extract API tokens.
3. **Top-Level Navigation Phishing**:
   - Forcing `window.top.location = "https://phishing-site.com"` to spoof login credentials.
4. **Reverse Tabnabbing**:
   - Opening hyperlinks with `target="_blank"` without `rel="noopener noreferrer"`, allowing the target page to manipulate `window.opener.location`.
5. **Unauthorized Network Exfiltration**:
   - Using background `fetch()` or `XMLHttpRequest` to transmit confidential prompt data to external command-and-control servers.

---

## 2. Dual-Defense Strategy

To support both **interactive web tools** (such as PMF calculators, sliders, and dynamic charts) and **static rich documents**, the system implements a dual-defense strategy:

| Feature | Tier 1: Iframe Sandbox (`SecureIframeRenderer`) | Tier 2: DOMPurify Sanitizer (`SanitizedHtmlRenderer`) |
| :--- | :--- | :--- |
| **Primary Use Case** | Interactive widgets, calculators, Tailwind UI | Static documents, PRDs, rich formatted text |
| **Script Execution** | Allowed, but strictly isolated in a `null` origin | **100% Blocked & Purged** |
| **Isolation Mechanism** | Browser process / context boundary (`sandbox`) | Node/Attribute AST Sanitization (`DOMPurify`) |
| **Parent DOM Access** | **Blocked** (Cross-origin security error) | Shared DOM (Safe because scripts are stripped) |
| **Cookie & Storage Access** | **Blocked** (Opaque partitioned origin) | Protected via strict script/event stripping |
| **Network Requests** | Blocked via Content Security Policy (`connect-src 'none'`) | Blocked via tag & protocol whitelisting |

---

## 3. Allowed Tags & Attributes (DOMPurify Whitelist)

### Allowed Tags
The sanitizer only permits safe semantic, structural, and declarative UI elements:

```typescript
export const ALLOWED_TAGS = [
  // Document Structure & Headings
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'section', 'article',
  'header', 'footer', 'main', 'aside', 'nav', 'hr', 'br',

  // Typography & Formatting
  'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'del', 'ins', 'mark', 'small',
  'sub', 'sup', 'blockquote', 'pre', 'code', 'kbd', 'samp',

  // Lists
  'ul', 'ol', 'li', 'dl', 'dt', 'dd',

  // Tabular Data
  'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',

  // Visual Assets & Safe Vector Graphics
  'img', 'svg', 'path', 'circle', 'rect', 'line', 'polygon', 'polyline', 'g',

  // Safe UI / Interactive Controls (no form submission or password capture)
  'button', 'label', 'input', 'select', 'option', 'progress', 'meter',

  // Hyperlinks (Enforced with rel="noopener noreferrer")
  'a'
];
```

### Allowed Attributes
- **Global / Accessibility**: `class`, `id`, `title`, `role`, `tabindex`, `aria-label`, `aria-hidden`, `aria-describedby`, `aria-expanded`
- **Media & SVGs**: `src`, `alt`, `width`, `height`, `loading`, `viewBox`, `fill`, `stroke`, `stroke-width`, `d`
- **Tables**: `colspan`, `rowspan`, `headers`, `scope`
- **Safe Input Controls**: `type`, `value`, `min`, `max`, `step`, `placeholder`, `disabled`, `checked`, `readonly` (sensitive types `password`, `file`, `hidden` are forcefully neutralized)
- **Styling**: `style` (sanitized against CSS injection and `url()` expressions)

---

## 4. Blocked Elements, Scripts & Attributes

### Blocked Elements (Purged from AST)
1. **Executable Scripts**: `<script>`, `<noscript>`
2. **External Plugins & Binaries**: `<object>`, `<embed>`, `<applet>`
3. **Arbitrary Browsing Contexts**: `<iframe>`, `<frame>`, `<frameset>`
4. **Document Hijacking & Metadata**: `<base>`, `<meta>`, `<link>`
5. **Data Exfiltration Forms**: `<form>`

### Blocked Attributes & Event Handlers
1. **All Inline Event Handlers**:
   - Every attribute starting with `on*` is unconditionally removed: `onclick`, `onload`, `onerror`, `onmouseover`, `onfocus`, `onchange`, `onsubmit`, `onkeydown`, etc.
2. **Dangerous URI Protocols**:
   - `javascript:` (e.g. `<a href="javascript:alert(1)">`)
   - `vbscript:`
   - `data:text/html`
   - `data:application/javascript`

---

## 5. Security Reasoning & Sandbox Design

### Why Omit `allow-same-origin` in Iframe Sandbox?
> [!CAUTION]
> Combining `sandbox="allow-scripts allow-same-origin"` on the same host completely defeats sandbox isolation.
>
> If `allow-same-origin` is included, the sandboxed script has the same origin as the parent application. The script could programmatically access `window.parent.document`, read `localStorage`, steal session cookies, or even mutate the `sandbox` attribute itself.

By **omitting `allow-same-origin`**, the browser assigns the iframe a unique, opaque **`null` origin**. This guarantees that:
- Any call to `window.parent.document` or `window.top.localStorage` immediately throws a `DOMException: Blocked a frame with origin "null" from accessing a cross-origin frame`.
- The iframe cannot access or share HTTP cookies with the host application.
- The iframe cannot forge authenticated same-origin API requests to `/chat` or `/artifacts`.

### Why Omit `allow-top-navigation`?
Without `allow-top-navigation`, the sandboxed document is forbidden from redirecting the parent window. If a hallucinated or injected payload executes `window.top.location = "https://malicious-phishing.com"`, the browser blocks the navigation attempt.

### Content Security Policy (CSP) Reinforcement
In addition to the iframe sandbox, the `srcdoc` includes a restrictive Content Security Policy:
```http
Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline' https://cdn.tailwindcss.com; style-src 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com; font-src https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'none'; frame-src 'none'; object-src 'none';
```
- `connect-src 'none'`: Prevents the sandboxed script from making unauthorized background network calls (`fetch`, `XMLHttpRequest`, `WebSocket`) to external exfiltration endpoints.
- `object-src 'none'`: Completely disables Flash, Java, and plugin execution.
- `frame-src 'none'`: Prevents clickjacking and nested frame hierarchies.

### Reverse Tabnabbing Defense
For all hyperlinks (`<a>`), DOMPurify hooks enforce:
```html
<a href="https://example.com" target="_blank" rel="noopener noreferrer">
```
- `rel="noopener"`: Ensures the target window cannot reference `window.opener`, preventing the external page from manipulating the parent URL.
- `rel="noreferrer"`: Prevents leaking the referrer header and confidential URL parameters to destination servers.
