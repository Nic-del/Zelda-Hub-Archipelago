--
ENABLE_DEBUG_LOG = true

ScriptHost:LoadScript("scripts/control.lua")
ScriptHost:LoadScript("scripts/autotracking.lua")



--
Tracker:AddItems("items/items.json")
Tracker:AddItems("items/dungeonnames.json")
Tracker:AddItems("items/item_settings.json")



--
Tracker:AddMaps("maps/maps.json")



--
Tracker:AddLayouts("layouts/tracker.json")

Tracker:AddLayouts("layouts/item_grid.json")
Tracker:AddLayouts("layouts/bugs.json")
Tracker:AddLayouts("layouts/keys_bosses.json")
Tracker:AddLayouts("layouts/portals.json")

Tracker:AddLayouts("layouts/layout_settings.json")
Tracker:AddLayouts("layouts/broadcast_items.json")


Tracker:AddLayouts("layouts/layouts_maps.json")

--
Tracker:AddLocations("locations/rooms/overworld.json")
Tracker:AddLocations("locations/rooms/ft.json")
Tracker:AddLocations("locations/rooms/gm.json")
Tracker:AddLocations("locations/rooms/lt.json")
Tracker:AddLocations("locations/rooms/ag.json")
Tracker:AddLocations("locations/rooms/sr.json")
Tracker:AddLocations("locations/rooms/tt.json")
Tracker:AddLocations("locations/rooms/cs.json")
Tracker:AddLocations("locations/rooms/pt.json")
Tracker:AddLocations("locations/rooms/hc.json")

Tracker:AddLocations("locations/overworld/castle town.json")
Tracker:AddLocations("locations/overworld/eldin.json")
Tracker:AddLocations("locations/overworld/faron.json")
Tracker:AddLocations("locations/overworld/gerudo desert.json")
Tracker:AddLocations("locations/overworld/lanayru.json")
Tracker:AddLocations("locations/overworld/ordon.json")
Tracker:AddLocations("locations/overworld/sacred grove.json")
Tracker:AddLocations("locations/overworld/snowpeak mountain.json")
Tracker:AddLocations("locations/overworld/main map.json")
Tracker:AddLocations("locations/overworld/main map dungeons.json")
Tracker:AddLocations("locations/overworld/regions.json")

Tracker:AddLocations("locations/dungeons/forest temple.json")
Tracker:AddLocations("locations/dungeons/goron mines.json")
Tracker:AddLocations("locations/dungeons/lakebed temple.json")
Tracker:AddLocations("locations/dungeons/arbiter's grounds.json")
Tracker:AddLocations("locations/dungeons/snowpeak ruins.json")
Tracker:AddLocations("locations/dungeons/temple of time.json")
Tracker:AddLocations("locations/dungeons/city in the sky.json")
Tracker:AddLocations("locations/dungeons/palace of twilight.json")
Tracker:AddLocations("locations/dungeons/hyrule castle.json")


ScriptHost:LoadScript("scripts/code_watchers.lua")