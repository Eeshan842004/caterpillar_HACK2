export interface Lesson {
  id: string;
  title: string;
  duration: string;
  reason: string;
  summary: string;
  steps: string[];
  question: string;
  choices: string[];
  answer: number;
}

export const LESSONS: Lesson[] = [
  {
    id: 'safe-exit',
    title: 'Secure before exiting',
    duration: '3 min',
    reason: 'Recommended for today’s excavator work',
    summary: 'Use a consistent shutdown sequence before leaving the cab. Throughline checks the available signals, but it never replaces the machine procedure.',
    steps: ['Stop machine motion on stable ground.', 'Lower the implement and place the controls in neutral.', 'Engage the hydraulic lockout or parking brake.', 'Check the area, then maintain three points of contact while exiting.'],
    question: 'Which action should happen before leaving the cab?',
    choices: ['Engage the secure control and lower the implement', 'Leave the engine at working speed', 'Rely only on the tablet checklist'],
    answer: 0,
  },
  {
    id: 'proximity',
    title: 'Respond to a proximity alert',
    duration: '4 min',
    reason: 'Relevant to trench and loading zones',
    summary: 'A proximity alert describes an object, its position and urgency. Confirm the real scene before continuing work.',
    steps: ['Stop or slow as the alert instructs.', 'Use mirrors and direct observation to locate the hazard.', 'Do not continue until the exclusion zone is clear.', 'Treat an unavailable sensor as unavailable—not as a clear area.'],
    question: 'What does “Proximity unavailable” mean?',
    choices: ['The area is clear', 'The system cannot confirm whether the area is clear', 'The detected person has moved away'],
    answer: 1,
  },
  {
    id: 'seatbelt',
    title: 'Seatbelt alerts during operation',
    duration: '2 min',
    reason: 'Supports the active safety check',
    summary: 'Throughline distinguishes operation from travel. An unfastened belt while travelling receives the highest urgency.',
    steps: ['Fasten the belt before releasing the machine’s secure control.', 'Keep it fastened while working or travelling.', 'If an alert appears, reach a safe state and fasten the belt.', 'Acknowledging an alert does not remove the underlying hazard.'],
    question: 'Does acknowledging a seatbelt alert make the condition safe?',
    choices: ['Yes', 'Only at low speed', 'No, the belt must be fastened'],
    answer: 2,
  },
];

export function lessonSpeech(lesson: Lesson): string {
  return `${lesson.title}. ${lesson.summary} ${lesson.steps.map((step, index) => `Step ${index + 1}. ${step}`).join(' ')}`;
}
