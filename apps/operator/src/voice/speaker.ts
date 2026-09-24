// Speaker (F5-R4, F11-R4): higher-priority speech interrupts lower (§8.3). Device TTS is the fallback until the
// recorded alert clips (E-05) are added; A14 shows that clips are not installed yet.
import * as Speech from 'expo-speech';

let currentPriority: number | null = null;

export function speak(text: string, priority: number): void {
  if (currentPriority !== null && priority > currentPriority) return; // a more urgent message is playing
  if (currentPriority !== null) Speech.stop();
  currentPriority = priority;
  try {
    Speech.speak(text, {
      language: 'en-IN',
      rate: 1.0,
      onDone: () => { currentPriority = null; },
      onStopped: () => { currentPriority = null; },
      onError: () => { currentPriority = null; },
    });
  } catch {
    currentPriority = null; // TTS unavailable: text stays on screen (never blocks the UI)
  }
}

export function stopSpeaking(): void {
  Speech.stop();
  currentPriority = null;
}
