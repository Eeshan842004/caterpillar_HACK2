// Root layout: providers, status bar, global overlays and ModeGuard (technical spec §4.4 app/_layout, §7.4.1).
import { Slot, usePathname, useRouter } from 'expo-router';
import { useEffect, useRef } from 'react';
import { View } from 'react-native';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { useHost } from '../src/engine/host';
import { KeyInputProvider } from '../src/input/keys';
import { PresenterPanel } from '../src/sim/PresenterPanel';
import { AppStatusBar, usePalette } from '../src/ui/components';
import { AlertOverlay, MenuOverlay, PromptSheet, SafeExitOverlay, VoiceOverlay } from '../src/ui/overlays';

const MODE_ROUTES = ['/focus', '/drive'];

function ModeGuard() {
  const router = useRouter();
  const path = usePathname();
  const paired = useHost((s) => s.paired);
  const signedIn = useHost((s) => !!s.snapshot?.shift);
  const state = useHost((s) => s.snapshot?.machine.state);
  const lastMenu = useRef('/tasks');

  useEffect(() => {
    if (!MODE_ROUTES.includes(path) && path !== '/setup' && path !== '/sign-in' && path !== '/') lastMenu.current = path;
  }, [path]);

  useEffect(() => {
    if (!paired) {
      if (path !== '/setup') router.replace('/setup');
      return;
    }
    if (!signedIn) {
      if (path !== '/sign-in') router.replace('/sign-in');
      return;
    }
    if (path === '/setup' || path === '/sign-in' || path === '/') {
      router.replace('/briefing');
      return;
    }
    if (state === 'WORKING' && path !== '/focus') router.replace('/focus');
    else if (state === 'TRAVELLING' && path !== '/drive') router.replace('/drive');
    else if ((state === 'OFF' || state === 'SECURED' || state === 'READY') && MODE_ROUTES.includes(path)) {
      router.replace(lastMenu.current as never);
    }
    // UNKNOWN keeps the current route (and locks menus) — conservative behaviour (F5-R7)
  }, [paired, signedIn, state, path, router]);
  return null;
}

function Shell() {
  const p = usePalette();
  return (
    <View style={{ flex: 1, backgroundColor: p.bg }}>
      <AppStatusBar />
      <AlertOverlay />
      <View style={{ flex: 1 }}>
        <Slot />
        <PromptSheet />
        <MenuOverlay />
        <VoiceOverlay />
      </View>
      <SafeExitOverlay />
      <PresenterPanel />
      <ModeGuard />
    </View>
  );
}

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <KeyInputProvider>
        <Shell />
      </KeyInputProvider>
    </SafeAreaProvider>
  );
}
