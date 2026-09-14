/**
 * Secure HTML Sanitizer and Security Policy Definition.
 *
 * Implements strict defense-in-depth sanitization against Cross-Site Scripting (XSS),
 * Clickjacking, and Reverse Tabnabbing.
 */

import DOMPurify from 'dompurify';
import { SecurityPolicyInfo, SecureRenderingMode } from '../types';

// ==============================================================================
// 1. Tag & Attribute Whitelists (Defense-in-Depth)
// ==============================================================================

/**
 * Allowed HTML tags. Only safe presentation, structure, and declarative UI elements.
 * All executable tags (script, object, iframe, embed) are strictly excluded.
 */
export const ALLOWED_TAGS: string[] = [
  // Document Structure & Headings
  'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span', 'section', 'article',
  'header', 'footer', 'main', 'aside', 'nav', 'hr', 'br',

  // Typography & Formatting
  'strong', 'b', 'em', 'i', 'u', 's', 'strike', 'del', 'ins', 'mark', 'small',
  'sub', 'sup', 'blockquote', 'pre', 'code', 'kbd', 'samp',

  // Lists
  'ul', 'ol', 'li', 'dl', 'dt', 'dd',

  // Tables
  'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption', 'colgroup', 'col',

  // Visual Assets & Safe SVG
  'img', 'svg', 'path', 'circle', 'rect', 'line', 'polygon', 'polyline', 'g',

  // Safe UI / Interactive Controls (no form submission or password capture)
  'button', 'label', 'input', 'select', 'option', 'progress', 'meter',

  // Navigation Links (enforced with rel="noopener noreferrer")
  'a',
];

/**
 * Allowed HTML attributes.
 * Inline event handlers (on*) and executable pseudo-protocols are strictly blocked.
 */
export const ALLOWED_ATTRIBUTES: string[] = [
  // Global presentation & accessibility
  'class', 'id', 'title', 'role', 'tabindex',
  'aria-label', 'aria-hidden', 'aria-describedby', 'aria-expanded',

  // Text & Link attributes
  'href', 'target', 'rel',

  // Media & SVG attributes
  'src', 'alt', 'width', 'height', 'loading',
  'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin', 'd',

  // Table attributes
  'colspan', 'rowspan', 'headers', 'scope',

  // Safe input attributes (range sliders, counters, checkboxes)
  'type', 'value', 'min', 'max', 'step', 'placeholder', 'disabled', 'checked', 'readonly',

  // Sanitized styling
  'style',
];

/**
 * Elements strictly blocked and purged from the DOM (along with their child nodes).
 */
export const BLOCKED_ELEMENTS: string[] = [
  'script',    // Executable JavaScript blocks
  'iframe',    // Nested arbitrary browsing contexts
  'object',    // Browser plugins / ActiveX / Flash
  'embed',     // External plugin media
  'applet',    // Java applets
  'form',      // Unauthorized data exfiltration forms
  'base',      // Base URI hijacking attacks
  'meta',      // Arbitrary redirect & charset manipulation
  'link',      // External CSS stylesheet hijacking
  'noscript',  // Alternative script bypass vectors
];

/**
 * Blocked URL protocols to prevent javascript: pseudo-protocol XSS.
 */
export const BLOCKED_PROTOCOLS: string[] = [
  'javascript:',
  'vbscript:',
  'data:text/html',
  'data:application/javascript',
];

// ==============================================================================
// 2. DOMPurify Sanitization Engine
// ==============================================================================

/**
 * Configure DOMPurify instance with strict security rules and hooks.
 */
function createConfiguredPurifier() {
  // If running in browser environment with DOMPurify
  if (typeof window !== 'undefined' && DOMPurify && typeof DOMPurify.sanitize === 'function') {
    // Add hook to enforce safe external link behavior
    DOMPurify.removeHook('afterSanitizeAttributes');
    DOMPurify.addHook('afterSanitizeAttributes', (node) => {
      // 1. Secure all hyperlinks
      if (node.tagName === 'A') {
        const href = node.getAttribute('href') || '';
        // Ensure no javascript: links slip through
        if (BLOCKED_PROTOCOLS.some((proto) => href.toLowerCase().trim().startsWith(proto))) {
          node.removeAttribute('href');
        } else {
          // Force secure new-tab navigation to prevent Reverse Tabnabbing
          node.setAttribute('target', '_blank');
          node.setAttribute('rel', 'noopener noreferrer');
        }
      }

      // 2. Block sensitive input types (e.g. password theft or file uploads)
      if (node.tagName === 'INPUT') {
        const type = (node.getAttribute('type') || 'text').toLowerCase();
        if (['password', 'file', 'hidden'].includes(type)) {
          node.setAttribute('type', 'text');
        }
      }
    });

    return DOMPurify;
  }
  return null;
}

/**
 * Fallback DOM sanitizer using the browser's native DOMParser when DOMPurify
 * is initializing or in standalone testing environments.
 */
function fallbackDomSanitize(rawHtml: string): string {
  if (typeof window === 'undefined' || typeof DOMParser === 'undefined') {
    return rawHtml.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
  }

  const parser = new DOMParser();
  const doc = parser.parseFromString(rawHtml, 'text/html');

  // Recursively sanitize DOM nodes
  function cleanNode(node: Node) {
    if (node.nodeType === Node.ELEMENT_NODE) {
      const el = node as HTMLElement;
      const tag = el.tagName.toLowerCase();

      // Remove blocked tags immediately
      if (BLOCKED_ELEMENTS.includes(tag) || !ALLOWED_TAGS.includes(tag)) {
        el.remove();
        return;
      }

      // Strip disallowed or dangerous attributes
      const attrs = Array.from(el.attributes);
      for (const attr of attrs) {
        const attrName = attr.name.toLowerCase();
        const attrValue = attr.value.toLowerCase().trim();

        // Strip inline event handlers (onclick, onerror, onload, etc.)
        if (attrName.startsWith('on')) {
          el.removeAttribute(attr.name);
          continue;
        }

        // Check for blocked protocols in URI attributes
        if (['href', 'src', 'action'].includes(attrName)) {
          if (BLOCKED_PROTOCOLS.some((proto) => attrValue.startsWith(proto))) {
            el.removeAttribute(attr.name);
            continue;
          }
        }

        // Check whitelist
        if (!ALLOWED_ATTRIBUTES.includes(attrName) && !attrName.startsWith('data-') && !attrName.startsWith('aria-')) {
          el.removeAttribute(attr.name);
        }
      }

      // Enforce noopener noreferrer on links
      if (tag === 'a') {
        el.setAttribute('target', '_blank');
        el.setAttribute('rel', 'noopener noreferrer');
      }
    }

    // Traverse children
    const children = Array.from(node.childNodes);
    for (const child of children) {
      cleanNode(child);
    }
  }

  Array.from(doc.body.childNodes).forEach(cleanNode);
  return doc.body.innerHTML;
}

/**
 * Sanitize untrusted HTML content against XSS and injection attacks.
 */
export function sanitizeHtml(rawHtml: string): string {
  if (!rawHtml || typeof rawHtml !== 'string') return '';

  const purifier = createConfiguredPurifier();
  if (purifier) {
    return purifier.sanitize(rawHtml, {
      ALLOWED_TAGS,
      ALLOWED_ATTR: ALLOWED_ATTRIBUTES,
      FORBID_TAGS: BLOCKED_ELEMENTS,
      FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onchange'],
      ALLOW_DATA_ATTR: true,
      ADD_ATTR: ['target'],
    });
  }

  return fallbackDomSanitize(rawHtml);
}

// ==============================================================================
// 3. Iframe Sandbox Policy Configuration
// ==============================================================================

/**
 * Strict Sandbox flags for iframe rendering.
 *
 * NOTE on `allow-same-origin`:
 * We intentionally OMIT `allow-same-origin`!
 * By omitting `allow-same-origin`, the framed content is treated as coming from
 * a unique opaque origin (`null`). Even with `allow-scripts`, the script CANNOT:
 * - Read parent `localStorage`, `sessionStorage`, or `document.cookie`
 * - Access or manipulate the parent window (`window.parent` / `window.top`)
 * - Make authenticated same-origin API requests
 * - Remove its own sandbox attributes
 */
export const SANDBOX_FLAGS = [
  'allow-scripts', // Allows running interactive sliders, calculators, and vanilla JS
] as const;

export const SANDBOX_ATTRIBUTE_VALUE = SANDBOX_FLAGS.join(' ');

/**
 * Content Security Policy (CSP) injected directly into sandboxed iframe `srcdoc`.
 * Restricts external resources and blocks dangerous script injection.
 */
export const IFRAME_CSP_POLICY = [
  "default-src 'none'",
  "script-src 'unsafe-inline' https://cdn.tailwindcss.com",
  "style-src 'unsafe-inline' https://fonts.googleapis.com https://cdn.tailwindcss.com",
  "font-src https://fonts.gstatic.com",
  "img-src 'self' data: https:",
  "connect-src 'none'", // Disallow unauthorized external network requests
  "frame-src 'none'",   // Disallow nested frames
  "object-src 'none'",  // Disallow plugins
].join('; ');

/**
 * Wraps raw HTML into a complete, isolated document with embedded CSP metadata.
 */
export function buildSandboxedSrcDoc(htmlContent: string): string {
  // If the document already contains <!DOCTYPE html> or <html>, inject CSP into <head>
  if (htmlContent.includes('<head>')) {
    return htmlContent.replace(
      '<head>',
      `<head>\n  <meta http-equiv="Content-Security-Policy" content="${IFRAME_CSP_POLICY}">`
    );
  }

  // Otherwise, wrap it in a standard HTML5 shell
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="${IFRAME_CSP_POLICY}">
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-50 p-6 min-h-screen">
  ${htmlContent}
</body>
</html>`;
}

// ==============================================================================
// 4. Security Explanation Provider
// ==============================================================================

export function getSecurityPolicyExplanation(mode: SecureRenderingMode): SecurityPolicyInfo {
  if (mode === 'iframe-sandbox') {
    return {
      mode: 'iframe-sandbox',
      sandboxFlags: ['allow-scripts'],
      allowedTags: ['* (All valid HTML5, CSS, and JS inside isolated null origin)'],
      blockedElements: [
        'window.parent / window.top (Blocked: Cross-origin restriction)',
        'localStorage & sessionStorage (Blocked: Null origin partition)',
        'document.cookie (Blocked: No parent cookie access)',
        'Top-level navigation (Blocked: Cannot redirect parent window)',
        'Nested iframes & object plugins (Blocked via CSP frame-src/object-src)',
      ],
      reasoning: (
        'The iframe sandbox uses an isolated null origin by deliberately omitting `allow-same-origin`. ' +
        'While `allow-scripts` enables interactive calculators and UI sliders, the script executes in ' +
        'a completely separate context with zero access to application state, auth tokens, or cookies. ' +
        'A restrictive Content Security Policy (CSP) further disables outbound network requests.'
      ),
    };
  }

  return {
    mode: 'sanitized-dom',
    sandboxFlags: ['N/A (Native DOM Sanitization)'],
    allowedTags: ALLOWED_TAGS,
    blockedElements: BLOCKED_ELEMENTS.concat([
      'All inline event handlers (onclick, onerror, onload, onchange, etc.)',
      'javascript: and data:text/html pseudo-protocols',
      'Arbitrary network forms and file input vectors',
    ]),
    reasoning: (
      'DOMPurify parses the HTML and validates every node and attribute against a strict whitelist. ' +
      'All executable tags (<script>, <object>, <iframe>) and event attributes (onload, onerror) are ' +
      'completely stripped from the DOM tree before insertion. Outgoing hyperlinks are forcefully ' +
      'tagged with rel="noopener noreferrer" and target="_blank" to prevent Reverse Tabnabbing.'
    ),
  };
}
