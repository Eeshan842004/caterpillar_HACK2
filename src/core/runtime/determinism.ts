/**
 * Injectable time and identifier boundaries.
 *
 * Production/demo defaults use the system clock and random identifiers.
 * Tests and deterministic replays can inject fixed/sequence implementations.
 */

export interface Clock {
  now(): Date;
}

export interface IdGenerator {
  next(prefix: string): string;
}

export class SystemClock implements Clock {
  public now(): Date {
    return new Date();
  }
}

export class RandomIdGenerator implements IdGenerator {
  public next(prefix: string): string {
    const time = Date.now().toString(36);
    const random = Math.random().toString(36).slice(2, 10);
    return `${prefix}_${time}_${random}`;
  }
}

export class FixedClock implements Clock {
  constructor(private readonly instant: string | Date) {}

  public now(): Date {
    return new Date(this.instant);
  }
}

export class SequenceIdGenerator implements IdGenerator {
  private sequence = 0;

  constructor(private readonly namespace = 'test') {}

  public next(prefix: string): string {
    this.sequence += 1;
    return `${prefix}_${this.namespace}_${this.sequence.toString().padStart(4, '0')}`;
  }
}

export const systemClock = new SystemClock();
export const randomIdGenerator = new RandomIdGenerator();
