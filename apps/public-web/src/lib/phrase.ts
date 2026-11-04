// Shared by the build-time sealer and the browser. Keep it free of Node imports.
export const normalizePhrase = (value: string) => value.trim().toLowerCase().replace(/\s+/g, ' ');
