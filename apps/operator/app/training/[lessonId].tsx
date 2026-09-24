import { useLocalSearchParams, useRouter } from 'expo-router';
import { useState } from 'react';
import { Pressable, View } from 'react-native';
import { LESSONS, lessonSpeech } from '../../src/training/content';
import { Row, Screen, Section, StateFlag, T, usePalette } from '../../src/ui/components';
import { space } from '../../src/ui/tokens';
import { speak, stopSpeaking } from '../../src/voice/speaker';

export default function LessonPlayer() {
  const p = usePalette();
  const router = useRouter();
  const { lessonId } = useLocalSearchParams<{ lessonId: string }>();
  const lesson = LESSONS.find((item) => item.id === lessonId);
  const [choice, setChoice] = useState<number | null>(null);
  if (!lesson) return <Screen title="Lesson unavailable" hints="Back returns to training"><Row focused onPress={() => router.replace('/training')}><T>Back to training</T></Row></Screen>;
  const correct = choice === lesson.answer;
  return <Screen title={lesson.title} hints="Use Read aloud for voice guidance · Back returns to training">
    <View style={{ flexDirection: 'row', gap: space.sm, flexWrap: 'wrap' }}>
      <Pressable onPress={() => speak(lessonSpeech(lesson), 4)} style={{ minHeight: 64, paddingHorizontal: space.xl, alignItems: 'center', justifyContent: 'center', backgroundColor: p.primaryBg, borderRadius: 4 }}><T variant="label" style={{ color: p.onPrimary }}>Read lesson aloud</T></Pressable>
      <Pressable onPress={stopSpeaking} style={{ minHeight: 64, paddingHorizontal: space.xl, alignItems: 'center', justifyContent: 'center', borderWidth: 2, borderColor: p.border, borderRadius: 4 }}><T variant="label">Stop voice</T></Pressable>
      <StateFlag tone="info" word={lesson.duration} />
    </View>
    <Section title="Why this matters"><T>{lesson.summary}</T></Section>
    <Section title="Safe sequence">
      {lesson.steps.map((step, index) => <View key={step} style={{ flexDirection: 'row', gap: space.md, paddingVertical: space.md, borderBottomWidth: 1, borderColor: p.border }}><T variant="heading">{index + 1}</T><T style={{ flex: 1 }}>{step}</T></View>)}
    </Section>
    <Section title="Check your understanding">
      <T variant="heading" style={{ marginBottom: space.md }}>{lesson.question}</T>
      {lesson.choices.map((answer, index) => <Row key={answer} focused={choice === index} onPress={() => setChoice(index)}><T>{answer}</T></Row>)}
      {choice !== null ? <View style={{ marginTop: space.md }}><StateFlag tone={correct ? 'ok' : 'warning'} word={correct ? 'Correct' : 'Try again'} detail={correct ? 'Lesson complete' : 'Review the safe sequence'} /></View> : null}
    </Section>
    <Row focused={false} onPress={() => { stopSpeaking(); router.replace('/training'); }}><T variant="heading">Back to training</T></Row>
  </Screen>;
}
