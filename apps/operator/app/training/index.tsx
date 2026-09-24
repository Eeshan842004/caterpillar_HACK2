import { useRouter } from 'expo-router';
import { View } from 'react-native';
import { LESSONS } from '../../src/training/content';
import { Row, Screen, Section, StateFlag, T } from '../../src/ui/components';
import { space } from '../../src/ui/tokens';

export default function TrainingHub() {
  const router = useRouter();
  return <Screen title="Training" hints="Tap a lesson to open · Back returns to tasks">
    <T muted>Short lessons stored on this device. Your learning history stays private in this demo.</T>
    <Section title="Recommended for this shift">
      <View style={{ gap: space.xs }}>
        {LESSONS.map((lesson, index) => <Row key={lesson.id} focused={index === 0} onPress={() => router.push(`/training/${lesson.id}` as never)}>
          <View style={{ flexDirection: 'row', alignItems: 'center', gap: space.md, flexWrap: 'wrap' }}>
            <T variant="heading" style={{ flex: 1 }}>{lesson.title}</T>
            <StateFlag tone="info" word={lesson.duration} />
          </View>
          <T muted>{lesson.reason}</T>
          <T variant="caption" muted>Available offline</T>
        </Row>)}
      </View>
    </Section>
    <Row focused={false} onPress={() => router.replace('/tasks')}><T variant="heading">Back to tasks</T></Row>
  </Screen>;
}
