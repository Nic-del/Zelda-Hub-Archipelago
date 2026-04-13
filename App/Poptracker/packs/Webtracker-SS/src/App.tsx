import { useLayoutEffect, useEffect } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { useStore } from 'react-redux';
import { Route, HashRouter as Router, Routes, useLocation } from 'react-router-dom';
import { MakeClientAvailable } from './archipelago/ClientHooks';
import type { ColorScheme } from './customization/ColorScheme';
import { colorSchemeSelector } from './customization/Selectors';
import ErrorPage from './miscPages/ErrorPage';
import FullAcknowledgement from './miscPages/FullAcknowledgement';
import Guide from './miscPages/guide/Guide';
import Options from './options/Options';
import type { RootState } from './store/Store';
import Tracker from './Tracker';

function createApplyColorSchemeListener() {
    let prevScheme: ColorScheme | undefined = undefined;
    return (colorScheme: ColorScheme) => {
        if (colorScheme === prevScheme) {
            return;
        }
        prevScheme = colorScheme;
        const html = document.querySelector('html')!;
        Object.entries(colorScheme).forEach(([key, val]) => {
            html.style.setProperty(`--scheme-${key}`, val.toString());
        });

        // https://stackoverflow.com/a/33890907
        function getContrastColor(r: number, g: number, b: number) {
            const brightness = r * 0.299 + g * 0.587 + b * 0.114;
            // Comments suggest 150 works better than 186 for some reason
            return brightness > 150 ? '#000000' : '#FFFFFF';
        }

        const interactColor = colorScheme.interact.slice(1);
        const [r, g, b] = [0, 2, 4].map((offset) =>
            parseInt(interactColor.slice(offset, offset + 2), 16),
        );
        html.style.setProperty(
            `--scheme-interact-text`,
            getContrastColor(r, g, b),
        );
    };
}

function StreamerModeHandler() {
    const location = useLocation();

    useEffect(() => {
        // However, the patterns are /:part and /tracker/:part
        // Let's check more accurately
        const parts = location.pathname.split('/').filter(Boolean);
        const isStreamer = (parts.length === 1 && parts[0] !== 'tracker' && parts[0] !== 'acknowledgement' && parts[0] !== 'guide') || 
                           (parts.length === 2 && parts[0] === 'tracker');

        if (isStreamer) {
            document.documentElement.classList.add('streamer-mode');
        } else {
            document.documentElement.classList.remove('streamer-mode');
        }
    }, [location]);

    return null;
}

function App() {
    const store = useStore<RootState>();
    useLayoutEffect(() => {
        const listener = createApplyColorSchemeListener();
        listener(colorSchemeSelector(store.getState()));
        return store.subscribe(() =>
            listener(colorSchemeSelector(store.getState())),
        );
    }, [store]);

    return (
        <MakeClientAvailable>
            <ErrorBoundary FallbackComponent={ErrorPage}>
                <Router basename={$PUBLIC_URL}>
                    <StreamerModeHandler />
                    <Routes>
                        <Route path="/" element={<Options />} />
                        <Route path="/:part" element={<Options />} />
                        <Route path="/tracker" element={<Tracker />} />
                        <Route path="/tracker/:part" element={<Tracker />} />
                        <Route
                            path="/acknowledgement"
                            element={<FullAcknowledgement />}
                        />
                        <Route path="/guide" element={<Guide />} />
                    </Routes>
                </Router>
            </ErrorBoundary>
        </MakeClientAvailable>
    );
}

export default App;
