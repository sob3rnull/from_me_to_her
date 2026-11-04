import { createCipheriv, pbkdf2Sync, randomBytes } from 'node:crypto';
import { normalizePhrase } from './phrase';

export type SealedDoor = { salt: string; iv: string; data: string; iterations: number };

const ITERATIONS = 310_000;
let sealed: SealedDoor | undefined;

// Runs at build time only. The vault address is encrypted with a phrase the
// visitor must know, so it never appears in the HTML or JavaScript.
export function sealDoor(): SealedDoor {
  if (sealed) return sealed;
  const url = process.env.NEXT_PUBLIC_VAULT_URL || 'http://localhost:3001';
  const isLocalDemo = /^http:\/\/(localhost|127\.0\.0\.1)(:\d+)?\/?$/.test(url);
  const phrase = process.env.DOOR_PHRASE || (isLocalDemo ? 'open sesame' : '');
  if (!phrase) {
    throw new Error('Set DOOR_PHRASE before building for a real vault address. Only local demo builds have a default.');
  }
  const salt = randomBytes(16);
  const iv = randomBytes(12);
  const key = pbkdf2Sync(normalizePhrase(phrase), salt, ITERATIONS, 32, 'sha256');
  const cipher = createCipheriv('aes-256-gcm', key, iv);
  // WebCrypto expects the auth tag appended to the ciphertext.
  const data = Buffer.concat([cipher.update(url, 'utf8'), cipher.final(), cipher.getAuthTag()]);
  sealed = { salt: salt.toString('base64'), iv: iv.toString('base64'), data: data.toString('base64'), iterations: ITERATIONS };
  return sealed;
}
