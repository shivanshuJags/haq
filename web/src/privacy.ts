// Same ID-number patterns as core/privacy.py. The server already removes these before reading the
// message; this hides them in the user's own chat bubble too, so they don't stay on screen.
const ID_PATTERNS = [
  /\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b/g, // Aadhaar
  /\b[A-Z]{5}\d{4}[A-Z]\b/gi, // PAN
  /\b[A-Z]{2}\s?\d{2}\s?\d{2}\s?\d{2}\s?[A-D]\b/gi, // UK National Insurance
  /\b\d{13,19}\b/g, // bank account / card
]

export function hideIdNumbers(text: string): string {
  return ID_PATTERNS.reduce((current, pattern) => current.replace(pattern, '••••'), text)
}
