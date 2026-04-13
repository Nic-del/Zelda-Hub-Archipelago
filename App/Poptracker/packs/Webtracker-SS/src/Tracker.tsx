import { useContext, useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Link, Navigate, useLocation, useParams } from 'react-router-dom';
import {
    ClientManagerContext,
    useApConnectionStatusString,
} from './archipelago/ClientHooks';
import CustomizationModal from './customization/CustomizationModal';
import {
    autoRegionLoadingSelector,
    hasCustomLayoutSelector,
} from './customization/Selectors';
import goddessCubesList_ from './data/goddessCubes2.json';
import stageToRegion from './data/stageToRegion.json';
import { DragAndDropContext } from './dragAndDrop/DragAndDrop';
import EntranceTracker from './entranceTracker/EntranceTracker';
import { ExportButton } from './ImportExport';
import { TrackerLayoutCustom } from './layouts/TrackerLayoutCustom';
import { TrackerLayout } from './layouts/TrackerLayouts';
import { clearAllLocalStorage, useSyncTrackerStateToLocalStorage } from './LocalStorage';
import LocationContextMenu from './locationTracker/LocationContextMenu';
import LocationGroupContextMenu from './locationTracker/LocationGroupContextMenu';
import type { InventoryItem } from './logic/Inventory';
import { isLogicLoadedSelector, logicSelector } from './logic/Selectors';
import { MakeTooltipsAvailable } from './tooltips/TooltipHooks';
import { bulkEditChecks, setItemCounts, syncState, type TrackerState } from './tracker/Slice';
import { useTrackerInterfaceReducer } from './tracker/TrackerInterfaceReducer';
import { ItemTrackerContainer } from './itemTracker/ItemTrackerContainer';
import { GRID_TRACKER_ASPECT_RATIO } from './itemTracker/GridTracker';
import GridTracker from './itemTracker/GridTracker';
import ItemTracker from './itemTracker/ItemTracker';
import WorldMap from './locationTracker/mapTracker/WorldMap';
import { LocationsEntrancesList } from './locationTracker/LocationsEntrancesList';
import { TextClient } from './hints/TextClient';
import DungeonTracker from './itemTracker/DungeonTracker';
import BasicCounters from './BasicCounters';
import { itemLayoutSelector } from './customization/Selectors';
import { type ItemLayout } from './customization/Slice';
import styles from './layouts/TrackerLayouts.module.css';

export default function TrackerContainer() {
    const logicLoaded = useSelector(isLogicLoadedSelector);

    // If we haven't loaded logic yet, redirect to the main menu,
    // which will take care of loading logic for us.
    if (!logicLoaded) {
        return <Navigate to="/" />;
    }

    return (
        <MakeTooltipsAvailable>
            <DragAndDropContext>
                <TrackerSync />
                <ArchipelagoIntegration />
                <Tracker />
            </DragAndDropContext>
            <TrackerStateSaver />
        </MakeTooltipsAvailable>
    );
}

// Separate component for cross-tab syncing
function TrackerSync() {
    const dispatch = useDispatch();
    useEffect(() => {
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'ssrTrackerState' && e.newValue) {
                // If anything changed in another tab, update ourselves
                const newState = JSON.parse(e.newValue);
                dispatch(syncState(newState));
            }
        };
        window.addEventListener('storage', handleStorageChange);
        return () => window.removeEventListener('storage', handleStorageChange);
    }, [dispatch]);
    return null;
}

// Split out into separate component to optimize rerenders
function TrackerStateSaver() {
    useSyncTrackerStateToLocalStorage();
    return null;
}

function ArchipelagoIntegration() {
    const logic = useSelector(logicSelector);
    const dispatch = useDispatch();
    const clientManager = useContext(ClientManagerContext);
    const autoRegionLoading = useSelector(autoRegionLoadingSelector);

    // Use a ref to store a mock trackerInterfaceDispatch for auto-region
    // Since trackerInterfaceState is local to components, we'll just ignore auto-region here
    // or we could move trackerInterfaceState to Redux, but that's a big change.

    useEffect(() => {
        const shortToFull: Record<string, string> = {};
        for (const [fullName, checkInfo] of Object.entries(logic.checks)) {
            shortToFull[checkInfo.name] = fullName;
        }
        const clientLocationCallback = (locs: string[]) => {
            dispatch(
                bulkEditChecks({
                    checks: locs.map((loc) => shortToFull[loc]),
                    markChecked: true,
                }),
            );
        };

        const clientCubeCallback = (cubeflags: number) => {
            const cubes = Array.from(goddessCubesList_);
            const struck = cubes
                .filter((_, index) => (cubeflags & (1 << index)) !== 0)
                .map((cubedata) => cubedata[1]);
            dispatch(
                bulkEditChecks({
                    checks: struck,
                    markChecked: true,
                }),
            );
        };

        const clientItemCallback = (inv: TrackerState['inventory']) => {
            const items: { item: InventoryItem; count: number }[] = [];
            for (const [item, count] of Object.entries(inv)) {
                items.push({ item: item as InventoryItem, count });
            }
            dispatch(setItemCounts(items));
        };

        const stageCallback = (_stage: string) => {
            // Auto region loading is disabled in stream views for now 
            // as they don't share the same trackerInterfaceState easily.
        };

        clientManager?.setLocationCallback(clientLocationCallback);
        clientManager?.setItemCallback(clientItemCallback);
        clientManager?.setNewStageCallback(stageCallback);
        clientManager?.setCubeCallback(clientCubeCallback);
    }, [dispatch, logic, clientManager]);

    return null;
}

function Tracker() {
    const location = useLocation();
    const { part } = useParams<{ part: string }>();
    const view = new URLSearchParams(location.search).get('view');
    const targetPart = part || view;

    const layoutParam = new URLSearchParams(location.search).get('layout');
    const layout = (layoutParam === 'grid' || layoutParam === 'inventory') ? layoutParam : undefined;

    if (targetPart) {
        return <StreamView part={targetPart} />;
    }

    return (
        <>
            <div
                style={{
                    width: '100vw',
                    height: '100vh',
                    overflow: 'hidden',
                    background: 'var(--scheme-background)',
                }}
            >
                <div
                    style={{
                        height: '95%',
                        position: 'relative',
                        display: 'flex',
                        flexFlow: 'row nowrap',
                    }}
                >
                    <TrackerContents layoutOverride={layout} />
                </div>
                <div
                    style={{
                        position: 'fixed',
                        bottom: 0,
                        left: 0,
                        width: '100%',
                        height: '5%',
                    }}
                >
                    <TrackerFooter />
                </div>
            </div>
        </>
    );
}

function TrackerContents({ layoutOverride }: { layoutOverride?: ItemLayout }) {
    const hasCustomLayout = useSelector(hasCustomLayoutSelector);
    // const reqDungeons = useSelector(requiredDungeonsSelector);
    const [trackerInterfaceState, trackerInterfaceDispatch] =
        useTrackerInterfaceReducer();
    const clientManager = useContext(ClientManagerContext);
    const autoRegionLoading = useSelector(autoRegionLoadingSelector);

    // Handle auto-region loading specifically in the main tracker
    useEffect(() => {
        const stageCallback = (stage: string) => {
            if (autoRegionLoading) {
                const region =
                    stageToRegion[stage as keyof typeof stageToRegion];
                if (region !== undefined) {
                    trackerInterfaceDispatch({
                        type: 'selectHintRegion',
                        hintRegion: region,
                    });
                }
            }
        };
        clientManager?.setNewStageCallback(stageCallback);
    }, [clientManager, autoRegionLoading, trackerInterfaceDispatch]);

    return (
        <>
            <LocationContextMenu />
            <LocationGroupContextMenu
                interfaceDispatch={trackerInterfaceDispatch}
            />
            {hasCustomLayout ? (
                <TrackerLayoutCustom
                    interfaceDispatch={trackerInterfaceDispatch}
                    interfaceState={trackerInterfaceState}
                />
            ) : (
                <TrackerLayout
                    interfaceDispatch={trackerInterfaceDispatch}
                    interfaceState={trackerInterfaceState}
                    layoutOverride={layoutOverride}
                />
            )}
        </>
    );
}

function TrackerFooter() {
    const [showCustomizationDialog, setShowCustomizationDialog] =
        useState(false);
    const [showEntranceDialog, setShowEntranceDialog] = useState(false);
    const statusString = useApConnectionStatusString();

    return (
        <>
            <div
                style={{
                    background: 'lightgrey',
                    width: '100%',
                    height: '100%',
                    alignContent: 'center',
                    display: 'flex',
                    flexFlow: 'row nowrap',
                    justifyContent: 'space-around',
                    alignItems: 'center',
                }}
            >
                <div style={{ color: '#000000' }}>{statusString}</div>
                <div>
                    <Link to="/">
                        <div className="tracker-button">← Options</div>
                    </Link>
                </div>
                <div>
                    <div
                        className="tracker-button"
                        onClick={() => {
                            const part = prompt("Part to open (items, map, locations, chat, dungeons, counters):", "items");
                            if (part) window.open(`/#/tracker/${part}`, '_blank', 'width=400,height=600');
                        }}
                        style={{ cursor: 'pointer' }}
                    >
                        🎥 Stream
                    </div>
                </div>
                <div>
                    <ExportButton />
                </div>
                <div>
                    <button
                        type="button"
                        className="tracker-button"
                        onClick={() => setShowEntranceDialog(true)}
                    >
                        Entrances
                    </button>
                </div>
                <div>
                    <button
                        type="button"
                        className="tracker-button"
                        onClick={() => setShowCustomizationDialog(true)}
                    >
                        Customization
                    </button>
                </div>
                <div>
                    <button
                        type="button"
                        className="tracker-button"
                        onClick={() => {
                            if (window.confirm('Voulez-vous vraiment réinitialiser le cache (localStorage) ? Cela va recharger la page.')) {
                                clearAllLocalStorage();
                            }
                        }}
                        style={{ backgroundColor: '#ff4444', color: 'white' }}
                    >
                        Reset Cache
                    </button>
                </div>
            </div>
            <CustomizationModal
                open={showCustomizationDialog}
                onOpenChange={setShowCustomizationDialog}
            />
            <EntranceTracker
                open={showEntranceDialog}
                onOpenChange={setShowEntranceDialog}
            />
        </>
    );
}

function StreamView({ part }: { part: string }) {
    const location = useLocation();
    const [confirmReset, setConfirmReset] = useState(false);
    const [trackerInterfaceState, trackerInterfaceDispatch] =
        useTrackerInterfaceReducer();
    const itemLayoutStore = useSelector(itemLayoutSelector);
    const layoutParam = new URLSearchParams(location.search).get('layout');
    const itemLayout = (layoutParam === 'grid' || layoutParam === 'inventory') ? layoutParam : itemLayoutStore;

    let content;
    switch (part) {
        case 'items':
            content = (
                <div style={{ padding: '4px', height: '100vh', display: 'flex', flexDirection: 'column' }}>
                    <ItemTrackerContainer
                        aspectRatio={GRID_TRACKER_ASPECT_RATIO}
                        itemTracker={(width) => (
                            itemLayout === 'grid'
                                ? <GridTracker width={width} />
                                : <ItemTracker width={width} />
                        )}
                    />
                </div>
            );
            break;
        case 'map':
            content = (
                <div style={{ padding: '10px', height: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <WorldMap
                        width={window.innerWidth - 40}
                        interfaceState={trackerInterfaceState}
                        interfaceDispatch={trackerInterfaceDispatch}
                    />
                </div>
            );
            break;
        case 'locations':
            content = (
                <div className={styles.scrollableBlock} style={{ height: '100vh', padding: '1rem' }}>
                    <LocationsEntrancesList
                        wide
                        includeHeader
                        interfaceState={trackerInterfaceState}
                        interfaceDispatch={trackerInterfaceDispatch}
                    />
                </div>
            );
            break;
        case 'chat':
            content = (
                <div className={styles.scrollableBlock} style={{ height: '100vh', padding: '1rem' }}>
                    <TextClient />
                </div>
            );
            break;
        case 'dungeons':
            content = (
                <div style={{ padding: '1rem' }}>
                    <DungeonTracker interfaceDispatch={trackerInterfaceDispatch} />
                </div>
            );
            break;
        case 'counters':
            content = (
                <div style={{ padding: '1rem' }}>
                    <BasicCounters />
                </div>
            );
            break;
        default:
            return <Navigate to="/tracker" />;
    }

    return (
        <div style={{
            height: '100vh',
            width: '100vw',
            overflow: 'hidden',
        }}>
            {content}
            <button
                type="button"
                onClick={() => {
                    if (!confirmReset) {
                        setConfirmReset(true);
                        setTimeout(() => setConfirmReset(false), 3000);
                    } else {
                        clearAllLocalStorage();
                    }
                }}
                style={{
                    position: 'fixed',
                    bottom: '5px',
                    right: '5px',
                    opacity: 0.7,
                    fontSize: '11px',
                    zIndex: 1000,
                    cursor: 'pointer',
                    background: confirmReset ? '#ff0000' : '#ff4444',
                    color: 'white',
                    border: '1px solid white',
                    borderRadius: '3px',
                    padding: '4px 8px',
                    fontWeight: 'bold',
                }}
                title="Vider le cache / Reset Cache"
            >
                {confirmReset ? "SÛR ? (CLIQUEZ ENCORE)" : "Reset Cache"}
            </button>
        </div>
    );
}
