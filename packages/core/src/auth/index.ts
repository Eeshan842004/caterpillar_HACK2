// PIN sign-in (technical spec §8.24, F1-R1): PBKDF2-HMAC-SHA256, 20 000 iterations, dkLen 32.
import { pbkdf2 } from '@noble/hashes/pbkdf2.js';
import { sha256 } from '@noble/hashes/sha2.js';
import { bytesToHex, hexToBytes, utf8ToBytes } from '@noble/hashes/utils.js';

export function hashPin(pin: string, saltHex: string, iterations: number): string {
  return bytesToHex(pbkdf2(sha256, utf8ToBytes(pin), hexToBytes(saltHex), { c: iterations, dkLen: 32 }));
}

export function verifyPin(pin: string, saltHex: string, hashHex: string, iterations: number): boolean {
  if (!/^\d{4,6}$/.test(pin)) return false;
  const got = hashPin(pin, saltHex, iterations);
  let diff = got.length ^ hashHex.length;
  for (let i = 0; i < Math.min(got.length, hashHex.length); i++) diff |= got.charCodeAt(i) ^ hashHex.charCodeAt(i);
  return diff === 0;
}

export interface LockoutState {
  failures: number;
  locked_until: number | null;
}

export function registerFailure(s: LockoutState, now: number): LockoutState {
  const failures = s.failures + 1;
  return failures >= 5 ? { failures: 0, locked_until: now + 60_000 } : { failures, locked_until: s.locked_until };
}

export function isLocked(s: LockoutState | undefined, now: number): boolean {
  return !!s?.locked_until && s.locked_until > now;
}
