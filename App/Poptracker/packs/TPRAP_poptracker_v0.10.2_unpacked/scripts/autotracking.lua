---@diagnostic disable: undefined-field
-- Configuration --------------------------------------
AUTOTRACKER_ENABLE_ITEM_TRACKING = true
AUTOTRACKER_ENABLE_LOCATION_TRACKING = true
AUTOTRACKER_ENABLE_DEBUG_LOGGING = true and ENABLE_DEBUG_LOG
AUTOTRACKER_ENABLE_DEBUG_LOGGING_AP = true and AUTOTRACKER_ENABLE_DEBUG_LOGGING
-------------------------------------------------------
function DebugLog()
	print("")
	print("Active Auto-Tracker Configuration")
	print("---------------------------------------------------------------------")
	print("Enable Item Tracking:		", AUTOTRACKER_ENABLE_ITEM_TRACKING)
	print("Enable Location Tracking:	", AUTOTRACKER_ENABLE_LOCATION_TRACKING)
	if AUTOTRACKER_ENABLE_DEBUG_LOGGING then
		print("Enable Debug Logging:		", AUTOTRACKER_ENABLE_DEBUG_LOGGING)
		print("Enable AP Debug Logging:		", AUTOTRACKER_ENABLE_DEBUG_LOGGING_AP)
	end
	print("---------------------------------------------------------------------")
	print("")
end
function DebugAP(msg)
	if AUTOTRACKER_ENABLE_DEBUG_LOGGING_AP then
		print(msg)
	end
end

ScriptHost:LoadScript("scripts/item_mapping.lua")
ScriptHost:LoadScript("scripts/location_mapping.lua")
ScriptHost:LoadScript("scripts/server_copy_keys.lua")
ScriptHost:LoadScript("scripts/region_mapping.lua")


CUR_INDEX = -1
SLOT_DATA = nil

function Dump_table(o, depth)
	if depth == nil then
		depth = 0
	end
	if type(o) == 'table' then
		local tabs = ('\t'):rep(depth)
		local tabs2 = ('\t'):rep(depth + 1)
		local s = '{\n'
		for k, v in pairs(o) do
			if type(k) ~= 'number' then
				k = '"' .. k .. '"'
			end
			s = s .. tabs2 .. '[' .. k .. '] = ' .. Dump_table(v, depth + 1) .. ',\n'
		end
		return s .. tabs .. '}'
	else
		return tostring(o)
	end
end

function ClearItems()
	for _, v in pairs(ITEM_MAPPING) do
		if v[1] and v[2] then
			DebugAP(string.format("onClear: clearing item '%s' of type '%s'", v[1], v[2]))
			local obj = Tracker:FindObjectForCode(v[1])
			if obj then
				if v[2] == "toggle" then
					obj.Active = false
				elseif v[2] == "progressive" then
					obj.CurrentStage = 0
					obj.Active = false
				elseif v[2] == "consumable" then
					obj.AcquiredCount = 0
				else 
					DebugAP(string.format("onClear: unknown item type '%s' for code '%s'", v[2], v[1]))
				end
			else
				DebugAP(string.format("onClear: could not find object for code '%s'", v[1]))
			end
		end
	end
	Tracker:FindObjectForCode("waterbomb").Active = false
	Tracker:FindObjectForCode("p_memory").CurrentStage = 0
	Tracker:FindObjectForCode("p_memory").Active = false
	Tracker:FindObjectForCode("youthsscent").Active = false
	Tracker:FindObjectForCode("iliascent").Active = false
	Tracker:FindObjectForCode("poescent").Active = false
	Tracker:FindObjectForCode("reekfishscent").Active = false
	Tracker:FindObjectForCode("medicinescent").Active = false
	Tracker:FindObjectForCode("faronvesseloflight").Active = false
	Tracker:FindObjectForCode("eldinvesseloflight").Active = false
	Tracker:FindObjectForCode("lanayruvesseloflight").Active = false
	Tracker:FindObjectForCode("fwkey").Active = false
	Tracker:FindObjectForCode("ftcompleted").Active = false
	Tracker:FindObjectForCode("gmcompleted").Active = false
	Tracker:FindObjectForCode("ltcompleted").Active = false
	Tracker:FindObjectForCode("agcompleted").Active = false
	Tracker:FindObjectForCode("srcompleted").Active = false
	Tracker:FindObjectForCode("ttcompleted").Active = false
	Tracker:FindObjectForCode("cscompleted").Active = false
	Tracker:FindObjectForCode("ptcompleted").Active = false
	Tracker:FindObjectForCode("hccompleted").Active = false
	Tracker:FindObjectForCode("dmhowlingstone").Active = false
	Tracker:FindObjectForCode("uzrhowlingstone").Active = false
	Tracker:FindObjectForCode("nfwhowlingstone").Active = false
	Tracker:FindObjectForCode("lhhowlingstone").Active = false
	Tracker:FindObjectForCode("smhowlingstone").Active = false
	Tracker:FindObjectForCode("hvhowlingstone").Active = false
end
function ClearLocations()
	for id, v in pairs(LOCATION_MAPPING) do
		if v[1] then
			DebugAP(string.format("onClear: clearing location '%s'", v[1]))
			local obj = Tracker:FindObjectForCode(v[1])
			if obj then
				if v[1]:sub(1, 1) == "@" then
					obj.AvailableChestCount = obj.ChestCount
				else
					obj.Active = false
				end
				ClearHints(id)
			else
				DebugAP(string.format("onClear: could not find object for code '%s'", v[1]))
			end
		end
	end
	Tracker:FindObjectForCode("@Hyrule Castle/5F/Victory/").AvailableChestCount = Tracker:FindObjectForCode("@Hyrule Castle/5F/Victory/").ChestCount
end
function ClearPortals()
	Tracker:FindObjectForCode("osportal").CurrentStage = 0
	Tracker:FindObjectForCode("sfwportal").CurrentStage = 0
	Tracker:FindObjectForCode("nfwportal").CurrentStage = 0
	Tracker:FindObjectForCode("kgportal").CurrentStage = 0
	Tracker:FindObjectForCode("kvportal").CurrentStage = 0
	Tracker:FindObjectForCode("dmportal").CurrentStage = 0
	Tracker:FindObjectForCode("boeportal").CurrentStage = 0
	Tracker:FindObjectForCode("zdportal").CurrentStage = 0
	Tracker:FindObjectForCode("lhportal").CurrentStage = 0
	Tracker:FindObjectForCode("ctportal").CurrentStage = 0
	Tracker:FindObjectForCode("uzrportal").CurrentStage = 0
	Tracker:FindObjectForCode("gmportal").CurrentStage = 0
	Tracker:FindObjectForCode("mcportal").CurrentStage = 0
	Tracker:FindObjectForCode("stportal").CurrentStage = 0
	Tracker:FindObjectForCode("sgportal").CurrentStage = 0
end
function SetSettings()
	if SLOT_DATA["World Version"] == "v0.2.2" or SLOT_DATA["World Version"] == "v0.2.1" or SLOT_DATA["World Version"] == "v0.2.0" or SLOT_DATA["World Version"] == "v0.1.5" or SLOT_DATA["World Version"] == "v0.1.3" or SLOT_DATA["World Version"] == "v0.1.2" or SLOT_DATA["World Version"] == "v0.1.1" or SLOT_DATA["World Version"] == "v0.1" then
		--skip if version is less than v0.2.3
	else
		if SLOT_DATA.Settings["Logic Settings"] == "Glitchless" then
			Tracker:FindObjectForCode("glitched").CurrentStage = 1
		elseif (SLOT_DATA.Settings["Logic Settings"] == "No Logic") or (SLOT_DATA.Settings["Logic Settings"] == "Glitched") then
			Tracker:FindObjectForCode("glitched").CurrentStage = 0
		end
		if SLOT_DATA.Settings["Poes Shuffled"] == "Yes" then
			Tracker:FindObjectForCode("poes").CurrentStage = 0
		elseif SLOT_DATA.Settings["Poes Shuffled"] == "No" then
			Tracker:FindObjectForCode("poes").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Golden Bugs Shuffled"] == "Yes" then
			Tracker:FindObjectForCode("gbugs").CurrentStage = 0
		elseif SLOT_DATA.Settings["Golden Bugs Shuffled"] == "No" then
			Tracker:FindObjectForCode("gbugs").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Castle Requirements"] == "Open" then
			Tracker:FindObjectForCode("castlerequirements").CurrentStage = 4
		elseif SLOT_DATA.Settings["Castle Requirements"] == "Fused Shadows" then
			Tracker:FindObjectForCode("castlerequirements").CurrentStage = 1
		elseif SLOT_DATA.Settings["Castle Requirements"] == "Mirror Shards" then
			Tracker:FindObjectForCode("castlerequirements").CurrentStage = 2
		elseif SLOT_DATA.Settings["Castle Requirements"] == "All Dungeons" then
			Tracker:FindObjectForCode("castlerequirements").CurrentStage = 3
		elseif SLOT_DATA.Settings["Castle Requirements"] == "Vanilla" then
			Tracker:FindObjectForCode("castlerequirements").CurrentStage = 0
		end
		if SLOT_DATA.Settings["Palace of Twilight Requirements"] == "Open" then
			Tracker:FindObjectForCode("palacerequirements").CurrentStage = 3
		elseif SLOT_DATA.Settings["Palace of Twilight Requirements"] == "Fused Shadows" then
			Tracker:FindObjectForCode("palacerequirements").CurrentStage = 1
		elseif SLOT_DATA.Settings["Palace of Twilight Requirements"] == "Mirror Shards" then
			Tracker:FindObjectForCode("palacerequirements").CurrentStage = 2
		elseif SLOT_DATA.Settings["Palace of Twilight Requirements"] == "Vanilla" then
			Tracker:FindObjectForCode("palacerequirements").CurrentStage = 0
		end
		if SLOT_DATA.Settings["Faron Woods Logic"] == "Open" then
			Tracker:FindObjectForCode("faronwoods").CurrentStage = 0
		elseif SLOT_DATA.Settings["Faron Woods Logic"] == "Closed" then
			Tracker:FindObjectForCode("faronwoods").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Lakebed Entrance Requirements"] == "Yes" then
			Tracker:FindObjectForCode("skiplakebedentrance").CurrentStage = 0
		elseif SLOT_DATA.Settings["Lakebed Entrance Requirements"] == "No" then
			Tracker:FindObjectForCode("skiplakebedentrance").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Arbiters Grounds Entrance Requirements"] == "Yes" then
			Tracker:FindObjectForCode("skiparbitersentrance").CurrentStage = 0
		elseif SLOT_DATA.Settings["Arbiters Grounds Entrance Requirements"] == "No" then
			Tracker:FindObjectForCode("skiparbitersentrance").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Snowpeak Entrance Requirements"] == "Yes" then
			Tracker:FindObjectForCode("skipsnowpeakentrance").CurrentStage = 0
		elseif SLOT_DATA.Settings["Snowpeak Entrance Requirements"] == "No" then
			Tracker:FindObjectForCode("skipsnowpeakentrance").CurrentStage = 1
		end
		if SLOT_DATA.Settings["City in the Sky Entrance Requirements"] == "Yes" then
			Tracker:FindObjectForCode("skipcityintheskyentrance").CurrentStage = 0
		elseif SLOT_DATA.Settings["City in the Sky Entrance Requirements"] == "No" then
			Tracker:FindObjectForCode("skipcityintheskyentrance").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Goron Mines Entrance Requirements"] == "Open" then
			Tracker:FindObjectForCode("goronminesentrance").CurrentStage = 0
		elseif SLOT_DATA.Settings["Goron Mines Entrance Requirements"] == "No Wrestling" then
			Tracker:FindObjectForCode("goronminesentrance").CurrentStage = 1
		elseif SLOT_DATA.Settings["Goron Mines Entrance Requirements"] == "Closed" then
			Tracker:FindObjectForCode("goronminesentrance").CurrentStage = 2
		end
		if SLOT_DATA.Settings["Temple of Time Entrance Requirements"] == "Open" then
			Tracker:FindObjectForCode("templeoftimeentrance").CurrentStage = 0
		elseif SLOT_DATA.Settings["Temple of Time Entrance Requirements"] == "Open Grove" then
			Tracker:FindObjectForCode("templeoftimeentrance").CurrentStage = 1
		elseif SLOT_DATA.Settings["Temple of Time Entrance Requirements"] == "Closed" then
			Tracker:FindObjectForCode("templeoftimeentrance").CurrentStage = 2
		end
		if SLOT_DATA.Settings["Skip Prologue"] == "Yes" then
			Tracker:FindObjectForCode("skipprologue").CurrentStage = 0
		end
		if SLOT_DATA.Settings["Faron Twilight Cleared"] == "Yes" then
			Tracker:FindObjectForCode("farontwilightcleared").CurrentStage = 0
		end
		if SLOT_DATA.Settings["Eldin Twilight Cleared"] == "Yes" then
			Tracker:FindObjectForCode("eldintwilightcleared").CurrentStage = 0
		end
		if SLOT_DATA.Settings["Lanayru Twilight Cleared"] == "Yes" then
			Tracker:FindObjectForCode("lanayrutwilightcleared").CurrentStage = 0
		end
		if SLOT_DATA.Settings["Skip MDH"] == "Yes" then
			Tracker:FindObjectForCode("skipmdh").CurrentStage = 0
		end
		if SLOT_DATA.Settings["Open Map"] == "Yes" then
			Tracker:FindObjectForCode("openmap").CurrentStage = 0
		elseif SLOT_DATA.Settings["Open Map"] == "No" then
			Tracker:FindObjectForCode("openmap").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Increase Wallet"] == "Yes" then
			Tracker:FindObjectForCode("increasewallet").CurrentStage = 0
		elseif SLOT_DATA.Settings["Increase Wallet"] == "No" then
			Tracker:FindObjectForCode("increasewallet").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Transform Anywhere"] == "Yes" then
			Tracker:FindObjectForCode("transformanywhere").CurrentStage = 0
		elseif SLOT_DATA.Settings["Transform Anywhere"] == "No" then
			Tracker:FindObjectForCode("transformanywhere").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Bonks do Damage"] == "Yes" then
			Tracker:FindObjectForCode("bonksdodamage").CurrentStage = 0
		elseif SLOT_DATA.Settings["Bonks do Damage"] == "No" then
			Tracker:FindObjectForCode("bonksdodamage").CurrentStage = 1
		end
		if SLOT_DATA.Settings["Damage Magnification"] == "Vanilla" then
			Tracker:FindObjectForCode("damagemagnification").CurrentStage = 0
		elseif SLOT_DATA.Settings["Damage Magnification"] == "Double" then
			Tracker:FindObjectForCode("damagemagnification").CurrentStage = 1
		elseif SLOT_DATA.Settings["Damage Magnification"] == "Triple" then
			Tracker:FindObjectForCode("damagemagnification").CurrentStage = 2
		elseif SLOT_DATA.Settings["Damage Magnification"] == "Quadruple" then
			Tracker:FindObjectForCode("damagemagnification").CurrentStage = 3
		elseif SLOT_DATA.Settings["Damage Magnification"] == "Ohko" then
			Tracker:FindObjectForCode("damagemagnification").CurrentStage = 4
		end
		if SLOT_DATA.Settings["Small Key Settings"] == "Vanilla" then
			Tracker:FindObjectForCode("smallkeys").CurrentStage = 0
		elseif SLOT_DATA.Settings["Small Key Settings"] == "Own Dungeon" then
			Tracker:FindObjectForCode("smallkeys").CurrentStage = 1
		elseif SLOT_DATA.Settings["Small Key Settings"] == "Any Dungeon" then
			Tracker:FindObjectForCode("smallkeys").CurrentStage = 2
		elseif SLOT_DATA.Settings["Small Key Settings"] == "Anywhere" then
			Tracker:FindObjectForCode("smallkeys").CurrentStage = 3
		elseif SLOT_DATA.Settings["Small Key Settings"] == "Start With" then
			Tracker:FindObjectForCode("smallkeys").CurrentStage = 4
		end
		if SLOT_DATA.Settings["Big Key Settings"] == "Vanilla" then
			Tracker:FindObjectForCode("bigkeys").CurrentStage = 0
		elseif SLOT_DATA.Settings["Big Key Settings"] == "Own Dungeon" then
			Tracker:FindObjectForCode("bigkeys").CurrentStage = 1
		elseif SLOT_DATA.Settings["Big Key Settings"] == "Any Dungeon" then
			Tracker:FindObjectForCode("bigkeys").CurrentStage = 2
		elseif SLOT_DATA.Settings["Big Key Settings"] == "Anywhere" then
			Tracker:FindObjectForCode("bigkeys").CurrentStage = 3
		elseif SLOT_DATA.Settings["Big Key Settings"] == "Start With" then
			Tracker:FindObjectForCode("bigkeys").CurrentStage = 4
		end
		if SLOT_DATA.Settings["Open Door of Time"] == "Yes" then
			Tracker:FindObjectForCode("dooroftime").CurrentStage = 0
		elseif SLOT_DATA.Settings["Open Door of Time"] == "No" then
			Tracker:FindObjectForCode("dooroftime").CurrentStage = 1
		end

		Tracker:AddLayouts("layouts/archipelago_keys.json")
		Tracker:AddLayouts("layouts/archipelago_item_grid.json")

		--Disable Hint Signs for current versions
		Tracker:FindObjectForCode("hints").CurrentStage = 1
	end
end
function InitPortals()
	if Tracker:FindObjectForCode("openmap").CurrentStage == 0 then
		Tracker:FindObjectForCode("osportal").CurrentStage = 1
		Tracker:FindObjectForCode("sfwportal").CurrentStage = 1
		Tracker:FindObjectForCode("nfwportal").CurrentStage = 1
		Tracker:FindObjectForCode("kgportal").CurrentStage = 1
		Tracker:FindObjectForCode("kvportal").CurrentStage = 1
		Tracker:FindObjectForCode("dmportal").CurrentStage = 1
		Tracker:FindObjectForCode("zdportal").CurrentStage = 1
		Tracker:FindObjectForCode("lhportal").CurrentStage = 1
		Tracker:FindObjectForCode("ctportal").CurrentStage = 1
		Tracker:FindObjectForCode("stportal").CurrentStage = 1
		Tracker:FindObjectForCode("sgportal").CurrentStage = 1
	end
end
function InitItems()
	Tracker:FindObjectForCode("faronvesseloflight").Active = true
	Tracker:FindObjectForCode("eldinvesseloflight").Active = true
	Tracker:FindObjectForCode("lanayruvesseloflight").Active = true
	Tracker:FindObjectForCode("fwkey").Active = true
end
function InitMap()
	Tracker:UiHint("ActivateTab", "Full Map")
	Tracker:UiHint("ActivateTab", "Overworld")
	Tracker:UiHint("ActivateTab", "Main Map")
end
function SetHintsFromSlotData()
	if SLOT_DATA["World Version"] == "v0.3.0" or SLOT_DATA["World Version"] == "v0.2.5" or SLOT_DATA["World Version"] == "v0.2.4" or SLOT_DATA["World Version"] == "v0.2.3" or SLOT_DATA["World Version"] == "v0.2.2" or SLOT_DATA["World Version"] == "v0.2.1" or SLOT_DATA["World Version"] == "v0.2.0" or SLOT_DATA["World Version"] == "v0.1.5" or SLOT_DATA["World Version"] == "v0.1.3" or SLOT_DATA["World Version"] == "v0.1.2" or SLOT_DATA["World Version"] == "v0.1.1" or SLOT_DATA["World Version"] == "v0.1" then
		--skip for up to v0.3.0
	else
		for k, v in pairs(SLOT_DATA.LocationClassification) do
			if v == "Excluded" then
				UpdateHints(tonumber(k), 10)
			elseif v == "Priority" then
				UpdateHints(tonumber(k), 30)
			end
		end
	end
end
function CorrectMistakes()
	if SLOT_DATA["World Version"] == "v0.2.3" then
		SLOT_DATA.Settings["Lakebed Entrance Requirements"] = SLOT_DATA.Settings["Lakebed Entrance Requirements"] or SLOT_DATA.Settings["Lakebed Enterance Requirements"]
		SLOT_DATA.Settings["Arbiters Grounds Entrance Requirements"] = SLOT_DATA.Settings["Arbiters Grounds Entrance Requirements"] or SLOT_DATA.Settings["Arbiters Grounds Requirements"]
		SLOT_DATA.Settings["Snowpeak Entrance Requirements"] = SLOT_DATA.Settings["Snowpeak Entrance Requirements"] or SLOT_DATA.Settings["Snowpeak Enterance Requirements"]
		SLOT_DATA.Settings["City in the Sky Entrance Requirements"] = SLOT_DATA.Settings["City in the Sky Entrance Requirements"] or SLOT_DATA.Settings["City in the Sky Enterance Requirements"]
		SLOT_DATA.Settings["Goron Mines Entrance Requirements"] = SLOT_DATA.Settings["Goron Mines Entrance Requirements"] or SLOT_DATA.Settings["Goron Mines Enterance Requirements"]
		SLOT_DATA.Settings["Temple of Time Entrance Requirements"] = SLOT_DATA.Settings["Temple of Time Entrance Requirements"] or SLOT_DATA.Settings["Temple of Time Enterance Requirements"]
		SLOT_DATA.Settings["Damage Magnification"] = SLOT_DATA.Settings["Damage Magnification"] or SLOT_DATA.Settings["Damage Magnifiation"]
	end
end


function OnClear(slot_data)
	DebugAP(string.format("called onClear, slot_data:\n%s", Dump_table(slot_data)))
	SLOT_DATA = slot_data
	print(Dump_table(SLOT_DATA))
	CorrectMistakes()
	CUR_INDEX = -1
	PLAYER_ID = Archipelago.PlayerNumber or -1
	TEAM_NUMBER = Archipelago.TeamNumber or 0
	if SLOT_DATA["World Version"] == "v0.2.3" or SLOT_DATA["World Version"] == "v0.2.2" or SLOT_DATA["World Version"] == "v0.2.1" or SLOT_DATA["World Version"] == "v0.2.0" or SLOT_DATA["World Version"] == "v0.1.5" or SLOT_DATA["World Version"] == "v0.1.3" or SLOT_DATA["World Version"] == "v0.1.2" or SLOT_DATA["World Version"] == "v0.1.1" or SLOT_DATA["World Version"] == "v0.1" then
		--skip if version is less than v0.2.4
	elseif SLOT_DATA["World Version"] == "v0.2.4" then
		Archipelago:SetNotify(SERVER_COPY)
		Archipelago:Get(SERVER_COPY)
	else --apply for all version v0.2.5+
		local server_copy = {}
		for _, sd in pairs(SERVER_COPY) do
			table.insert(server_copy, "TP_"..TEAM_NUMBER.."_"..PLAYER_ID.."_"..sd)
		end
		Archipelago:SetNotify(server_copy)
		Archipelago:Get(server_copy)
	end
	local game_beaten = {"_read_client_status_"..TEAM_NUMBER.."_"..PLAYER_ID}
	Archipelago:SetNotify(game_beaten)
	Archipelago:Get(game_beaten)
	local HINTS_ID = {"_read_hints_"..TEAM_NUMBER.."_"..PLAYER_ID}
	Archipelago:SetNotify(HINTS_ID)
	Archipelago:Get(HINTS_ID)
	
	ClearItems()
	ClearLocations()
	ClearPortals()
	SetSettings()
	InitPortals()
	InitItems()
	InitMap()
	SetHintsFromSlotData()
end

function OnItem(index, item_id, item_name, player_number)
	DebugAP(string.format("called onItem: index:'%s' id:'%s' name:'%s' player:'%s' cur_index:'%s'", index, item_id, item_name, player_number, CUR_INDEX))
	if not AUTOTRACKER_ENABLE_ITEM_TRACKING then
		return
	end
	if index <= CUR_INDEX then
		return
	end
	CUR_INDEX = index;
	local v = ITEM_MAPPING[item_id]
	if not v then
		DebugAP(string.format("onItem: could not find item mapping for id %s", item_id))
		return
	end
	DebugAP(string.format("onItem: code: %s, type %s", v[1], v[2]))
	if not v[1] then
		return
	end
	local obj = Tracker:FindObjectForCode(v[1])
	if obj then
		if v[1] == "bombbag" then
			Tracker:FindObjectForCode("waterbomb").Active = true
		end
		if v[2] == "toggle" then
			obj.Active = true
		elseif v[2] == "progressive" then
			if obj.Active then
				obj.CurrentStage = obj.CurrentStage + 1
			else
				obj.Active = true
			end
		elseif v[2] == "consumable" then
			obj.AcquiredCount = obj.AcquiredCount + obj.Increment
		else
			DebugAP(string.format("onItem: unknown item type %s for code %s", v[2], v[1]))
		end
	else
		DebugAP(string.format("onItem: could not find object for code %s", v[1]))
	end
end

function OnLocation(location_id, location_name)
	DebugAP(string.format("called onLocation: id:'%s' name:'%s'", location_id, location_name))
	if not AUTOTRACKER_ENABLE_LOCATION_TRACKING then
		return
	end
	local v = LOCATION_MAPPING[location_id]
	if not v then
		DebugAP(string.format("onLocation: could not find location mapping for id %s", location_id))
	end
	if not v[1] then
		return
	end
	local obj = Tracker:FindObjectForCode(v[1])
	if obj then
		if v[1]:sub(1, 1) == "@" then
			obj.AvailableChestCount = obj.AvailableChestCount - 1
		else
			obj.Active = true
		end
	else
		DebugAP(string.format("onLocation: could not find object for code %s", v[1]))
	end
end

function OnScout(location_id, location_name, item_id, item_name, item_player)
	DebugAP(string.format("called onScout: location:'%s', '%s' item:%s, %s, %s", location_id, location_name, item_id, item_name, item_player))
end

function OnBounce(json)
	DebugAP(string.format("called onBounce: %s", Dump_table(json)))
end

function OnNotify(_key, value, old)
	DebugAP(string.format("called onNotify: key:'%s' value:'%s' old_value:'%s'", _key, value, old))
	local key = _key
	if value == old then return end
	local _, _, team, player = string.find(_key, "_read_client_status_(.*)_(.*)")
	if team == ""..TEAM_NUMBER and player == ""..PLAYER_ID then
		local victory = value == 30
		Tracker:FindObjectForCode("hccompleted").Active = victory
		Tracker:FindObjectForCode("@Hyrule Castle/5F/Victory/").AvailableChestCount = Tracker:FindObjectForCode("@Hyrule Castle/5F/Victory/").AvailableChestCount - (victory and 1 or 0)
	end
	if SLOT_DATA["World Version"] == "v0.2.3" or SLOT_DATA["World Version"] == "v0.2.2" or SLOT_DATA["World Version"] == "v0.2.1" or SLOT_DATA["World Version"] == "v0.2.0" or SLOT_DATA["World Version"] == "v0.1.5" or SLOT_DATA["World Version"] == "v0.1.3" or SLOT_DATA["World Version"] == "v0.1.2" or SLOT_DATA["World Version"] == "v0.1.1" or SLOT_DATA["World Version"] == "v0.1" then
		--skip for up to v0.2.3
	else
		if SLOT_DATA["World Version"] == "v0.2.4" then
			--skip if v0.2.4
		else
			_, _, key = string.find(_key, "TP_.*_.*_(.*)")
		end
		if _key == "_read_hints_"..TEAM_NUMBER.."_"..PLAYER_ID and Highlight then
			for _, hint in ipairs(value) do
				if not hint.found and hint.finding_player == PLAYER_ID then
					UpdateHints(hint.location, hint.status)
				else
					ClearHints(hint.location)
				end
			end
		end
		if key == "Death Mountain Stone" then
			Tracker:FindObjectForCode("dmhowlingstone").Active = value
			Tracker:FindObjectForCode("@Eldin Region/Death Mountain Golden Wolves/Ordon Spring Stone/").AvailableChestCount = Tracker:FindObjectForCode("@Eldin Region/Death Mountain Golden Wolves/Ordon Spring Stone/").AvailableChestCount - (value and 1 or 0)
		elseif key == "Zora River Stone" then
			Tracker:FindObjectForCode("uzrhowlingstone").Active = value
			Tracker:FindObjectForCode("@Lanayru Region/Upper Zora's River Golden Wolves/West Castle Town Stone/").AvailableChestCount = Tracker:FindObjectForCode("@Lanayru Region/Upper Zora's River Golden Wolves/West Castle Town Stone/").AvailableChestCount - (value and 1 or 0)
		elseif key == "Sacred Grove Stone" then
			Tracker:FindObjectForCode("nfwhowlingstone").Active = value
			Tracker:FindObjectForCode("@Faron Region/Faron Woods Golden Wolves/South Castle Town Stone/").AvailableChestCount = Tracker:FindObjectForCode("@Faron Region/Faron Woods Golden Wolves/South Castle Town Stone/").AvailableChestCount - (value and 1 or 0)
		elseif key == "Lake Hylia Stone" then
			Tracker:FindObjectForCode("lhhowlingstone").Active = value
			Tracker:FindObjectForCode("@Gerudo Desert Golden Wolves/Lake Hylia Stone/").AvailableChestCount = Tracker:FindObjectForCode("@Gerudo Desert Golden Wolves/Lake Hylia Stone/").AvailableChestCount - (value and 1 or 0)
		elseif key == "Snowpeak Stone" then
			Tracker:FindObjectForCode("smhowlingstone").Active = value
			Tracker:FindObjectForCode("@Snowpeak Mountain Golden Wolves/Kakariko Graveyard Stone/").AvailableChestCount = Tracker:FindObjectForCode("@Snowpeak Mountain Golden Wolves/Kakariko Graveyard Stone/").AvailableChestCount - (value and 1 or 0)
		elseif key == "Hidden Village Stone" then
			Tracker:FindObjectForCode("hvhowlingstone").Active = value
			Tracker:FindObjectForCode("@Eldin Region/Hidden Village Golden Wolves/North Castle Town Stone/").AvailableChestCount = Tracker:FindObjectForCode("@Eldin Region/Hidden Village Golden Wolves/North Castle Town Stone/").AvailableChestCount - (value and 1 or 0)
		elseif key == "Youth Scent" then
			Tracker:FindObjectForCode("youthsscent").Active = value or (Tracker:FindObjectForCode("eldintwilightcleared").CurrentStage == 0)
		elseif key == "Ilias Scent" then
			Tracker:FindObjectForCode("iliascent").Active = value or (Tracker:FindObjectForCode("lanayrutwilightcleared").CurrentStage == 0)
		elseif key == "Medicine Scent" then
			Tracker:FindObjectForCode("medicinescent").Active = value
		elseif key == "ReekFish Scent" then
			Tracker:FindObjectForCode("reekfishscent").Active = value or (Tracker:FindObjectForCode("skipsnowpeakentrance").CurrentStage == 0)
		elseif key == "Poe Scent" then
			Tracker:FindObjectForCode("poescent").Active = value
		elseif key == "Renados letter" then
			if value == true then
				Tracker:FindObjectForCode("renadosletter").CurrentStage = Tracker:FindObjectForCode("renadosletter").CurrentStage + 1
			end
		elseif key == "Telmas Invoice" then
			if value == true then
				Tracker:FindObjectForCode("invoice").CurrentStage = Tracker:FindObjectForCode("invoice").CurrentStage + 1
			end
		elseif key == "Wooden Statue" then
			if value == true then
				Tracker:FindObjectForCode("woodenstatue").CurrentStage = Tracker:FindObjectForCode("woodenstatue").CurrentStage + 1
			end
		elseif key == "Ilias Charm" then
			if value == true then
				Tracker:FindObjectForCode("iliascharm").CurrentStage = Tracker:FindObjectForCode("iliascharm").CurrentStage + 1
			end
		elseif key == "Memory Reward" and Tracker:FindObjectForCode("horsecall").Active == false then
			Tracker:FindObjectForCode("horsecall").Active = value
		elseif key == "Zant Defeated" then
			Tracker:FindObjectForCode("ptcompleted").Active = value
		elseif key == "Stallord Defeated" then
			Tracker:FindObjectForCode("agcompleted").Active = value
		elseif key == "Argorok Defeated" then
			Tracker:FindObjectForCode("cscompleted").Active = value
		elseif key == "Diababa Defeated" then
			Tracker:FindObjectForCode("ftcompleted").Active = value
		elseif key == "Fyrus Defeated" then
			Tracker:FindObjectForCode("gmcompleted").Active = value
		elseif key == "Morpheel Defeated" then
			Tracker:FindObjectForCode("ltcompleted").Active = value
		elseif key == "Blizzeta Defeated" then
			Tracker:FindObjectForCode("srcompleted").Active = value
		elseif key == "Armogohma Defeated" then
			Tracker:FindObjectForCode("ttcompleted").Active = value
		end
		--if 0.3.0 or less
		if SLOT_DATA["World Version"] == "v0.3.0" or SLOT_DATA["World Version"] == "v0.2.5" or SLOT_DATA["World Version"] == "v0.2.4" or SLOT_DATA["World Version"] == "v0.2.3" or SLOT_DATA["World Version"] == "v0.2.2" or SLOT_DATA["World Version"] == "v0.2.1" or SLOT_DATA["World Version"] == "v0.2.0" or SLOT_DATA["World Version"] == "v0.1.5" or SLOT_DATA["World Version"] == "v0.1.3" or SLOT_DATA["World Version"] == "v0.1.2" or SLOT_DATA["World Version"] == "v0.1.1" or SLOT_DATA["World Version"] == "v0.1" then
			if key == "Current Region" and Tracker:FindObjectForCode("autotab").CurrentStage <= 1 then
				if REGION[value] ~= "Main Map" then
					Tracker:UiHint("ActivateTab", REGION[value])
					print("(v0.3.0) Changing Map to: "..REGION[value])
				end
				if REGION[value] == "Faron Woods" then
					Tracker:UiHint("ActivateTab", "Faron Woods")
					Tracker:UiHint("ActivateTab", "Faron")
					Tracker:UiHint("ActivateTab", "Overworld")
					print("(v0.3.0) Changing Map to: Faron Woods")
				end
				if REGION[value] == "Eldin Region" then
					Tracker:UiHint("ActivateTab", "Eldin Region")
					Tracker:UiHint("ActivateTab", "Eldin")
					Tracker:UiHint("ActivateTab", "Overworld")
					print("(v0.3.0) Changing Map to: Eldin Region")
				end
				if REGION[value] == "Lanayru Region" then
					Tracker:UiHint("ActivateTab", "Lanayru Region")
					Tracker:UiHint("ActivateTab", "Lanayru")
					Tracker:UiHint("ActivateTab", "Overworld")
					print("(v0.3.0) Changing Map to: Lanayru Region")
				end
				if REGION[value] == "Ordon" or
				REGION[value] == "Sacred Grove" or
				REGION[value] == "Snowpeak Mountain" or
				REGION[value] == "Castle Town" or
				REGION[value] == "Gerudo Desert" then
					Tracker:UiHint("ActivateTab", "Overworld")
					print("(v0.3.0) Changing Map to: "..REGION[value])
				end
				if REGION[value] == "Main Map" and Tracker:FindObjectForCode("autotab").CurrentStage == 1 then
					Tracker:UiHint("ActivateTab", "Overworld")
					Tracker:UiHint("ActivateTab", "Main Map")
					print("(v0.3.0) Changing Map to: "..REGION[value])
				end
			end
		else
			--if 0.4.0+
			if key == "Current Room" then
				CurrentRoom = value
				print("Current Room changed to: "..CurrentRoom)
				SwitchMap()
			elseif key == "Current Stage" then
				CurrentStage = STAGE[value]
				print("Current Stage changed to: "..CurrentStage)
				SwitchMap()
			elseif key == "Current Floor" then
				CurrentFloor = value
				print("Current Floor changed to: "..CurrentFloor)
				SwitchMap()
			end
		end
	end
end

function OnNotifyLaunch(key, value)
	DebugAP(string.format("called onNotifyLaunch: key:'%s', value:'%s'", key, value))
	OnNotify(key, value)
end


function UpdateHints(location_id, status)
	if not Highlight then return end
	local locations = LOCATION_MAPPING[location_id]
	for _, location in ipairs(locations) do
		local section = Tracker:FindObjectForCode(location)
		if section then
			print("Updating hint for "..location.." to status "..status)
			section.Highlight = PriorityToHighlight[status]
		else
			DebugAP(string.format("No object found for code: '%s'", location))
		end
	end
end
function ClearHints(locationID)
	if not Highlight then return end
	local locations = LOCATION_MAPPING[locationID]
	if not locations then return end
	for _, location in ipairs(locations) do
		local section = Tracker:FindObjectForCode(location)
		if section then
			print("Clearing hint for "..location)
			section.Highlight = Highlight.None
		else
			DebugAP(string.format("No object found for code: '%s'", location))
		end
	end
end

PriorityToHighlight = {}
if Highlight then
	PriorityToHighlight = {
		[0] = Highlight.Unspecified,
		[10] = Highlight.NoPriority,
		[20] = Highlight.Avoid,
		[30] = Highlight.Priority,
		[40] = Highlight.None -- found
	}
end

function Splitmapchange()
	if Tracker:FindObjectForCode("splitmap").CurrentStage == 0 then
		Tracker:AddLayouts("layouts/layouts_maps.json")
	elseif Tracker:FindObjectForCode("splitmap").CurrentStage == 1 then
		Tracker:AddLayouts("layouts/split_layouts_maps.json")
	end
end
function Broadcastchange()
	if Tracker:FindObjectForCode("broadcast").CurrentStage == 0 then
		Tracker:AddLayouts("layouts/broadcast_items.json")
	elseif Tracker:FindObjectForCode("broadcast").CurrentStage == 1 then
		Tracker:AddLayouts("layouts/broadcast_map.json")
	elseif Tracker:FindObjectForCode("broadcast").CurrentStage == 2 then
		Tracker:AddLayouts("layouts/broadcast_both.json")
	end
end
function Hidefrommainmap()
	if Tracker:FindObjectForCode("hidelayout").CurrentStage == 0 then
		Tracker:AddLayouts("layouts/tracker.json")
	elseif Tracker:FindObjectForCode("hidelayout").CurrentStage == 1 then
		Tracker:AddLayouts("layouts/tracker_no_map.json")
	elseif Tracker:FindObjectForCode("hidelayout").CurrentStage == 2 then
		Tracker:AddLayouts("layouts/tracker_no_items.json")
	end
end
function APLayoutchange()
	if Tracker:FindObjectForCode("aplayout").CurrentStage == 0 then
		Tracker:AddLayouts("layouts/keys_bosses.json")
		Tracker:AddLayouts("layouts/item_grid.json")
	elseif Tracker:FindObjectForCode("aplayout").CurrentStage == 1 then
		Tracker:AddLayouts("layouts/archipelago_keys.json")
		Tracker:AddLayouts("layouts/archipelago_item_grid.json")
	end
end
function Bugsamountchange()
	local n = 0
	for _, v in pairs(BUGS_ARRAY) do
		if Tracker:FindObjectForCode(v[2]).Active and Tracker:FindObjectForCode(v[1]).AvailableChestCount == 1 then
			n = n + 1
		end
	end
	if Tracker:FindObjectForCode("bugsamount").AcquiredCount ~= n then
		Tracker:FindObjectForCode("bugsamount").AcquiredCount = n
	end
end

function SwitchMap()
	if Tracker:FindObjectForCode("autotab").CurrentStage <= 1 then
		if CurrentStage == "Ordon" or
		CurrentStage == "Sacred Grove" or
		CurrentStage == "Snowpeak Mountain" or
		CurrentStage == "Gerudo Desert" or
		CurrentStage == "Castle Town" then
			Tracker:UiHint("ActivateTab", "Overworld")
			Tracker:UiHint("ActivateTab", CurrentStage)
			print("Changing Map to: "..CurrentStage)
		end
	end
	if Tracker:FindObjectForCode("autotab").CurrentStage == 0 then
		if CurrentStage == "Faron Woods" or
		CurrentStage == "Faron Field" or
		(CurrentStage == "Hyrule Field" and (CurrentRoom == 6 or CurrentRoom == 1 or CurrentRoom == 15)) then
			Tracker:UiHint("ActivateTab", "Overworld")
			Tracker:UiHint("ActivateTab", "Faron")
			Tracker:UiHint("ActivateTab", "Faron Region")
			print("Changing Map to: Faron Region ("..CurrentStage..")")
		elseif CurrentStage == "Kakariko Gorge" or
		CurrentStage == "Kakariko" or
		CurrentStage == "Death Mountain" or
		CurrentStage == "Eldin Field" or
		CurrentStage == "Hidden Village" or
		(CurrentStage == "Hyrule Field" and (CurrentRoom == 3 or CurrentRoom == 4 or CurrentRoom == 2 or CurrentRoom == 0 or CurrentRoom == 7 or CurrentRoom == 5)) then
			Tracker:UiHint("ActivateTab", "Overworld")
			Tracker:UiHint("ActivateTab", "Eldin")
			Tracker:UiHint("ActivateTab", "Eldin Region")
			print("Changing Map to: Eldin Region ("..CurrentStage..")")
		elseif CurrentStage == "Lake Hylia" or
		CurrentStage == "Lanayru Field" or
		CurrentStage == "Beside Castle Town" or
		CurrentStage == "South Castle Town" or
		CurrentStage == "Upper Zora's River" or
		CurrentStage == "Zora's Domain" or
		(CurrentStage == "Hyrule Field" and (CurrentRoom == 10 or CurrentRoom == 11 or CurrentRoom == 9 or CurrentRoom == 13 or CurrentRoom == 14 or CurrentRoom == 12)) then
			Tracker:UiHint("ActivateTab", "Overworld")
			Tracker:UiHint("ActivateTab", "Lanayru")
			Tracker:UiHint("ActivateTab", "Lanayru Region")
			print("Changing Map to: Lanayru Region ("..CurrentStage..")")
		elseif CurrentStage == "Forest Temple" or
		CurrentStage == "Goron Mines" or
		CurrentStage == "Lakebed Temple" or
		CurrentStage == "Arbiter's Grounds" or
		CurrentStage == "Snowpeak Ruins" or
		CurrentStage == "Temple of Time" or
		CurrentStage == "City in the Sky" or
		CurrentStage == "Palace of Twilight" or
		CurrentStage == "Hyrule Castle" then
			Tracker:UiHint("ActivateTab", CurrentStage)
			Tracker:UiHint("ActivateTab", "Full Map")
			print("Changing Map to: "..CurrentStage)
		end
	elseif Tracker:FindObjectForCode("autotab").CurrentStage == 1 then
		if CurrentStage == "Faron Woods" or
		CurrentStage == "Faron Field" then
			Tracker:UiHint("ActivateTab", "Overworld")
			Tracker:UiHint("ActivateTab", "Faron")
			Tracker:UiHint("ActivateTab", CurrentStage)
			print("Changing Map to: "..CurrentStage)
		elseif CurrentStage == "Kakariko Gorge" or
		CurrentStage == "Kakariko" or
		CurrentStage == "Death Mountain" or
		CurrentStage == "Eldin Field" or
		CurrentStage == "Hidden Village" then
			Tracker:UiHint("ActivateTab", "Overworld")
			Tracker:UiHint("ActivateTab", "Eldin")
			Tracker:UiHint("ActivateTab", CurrentStage)
			print("Changing Map to: "..CurrentStage)
		elseif CurrentStage == "Lake Hylia" or
		CurrentStage == "Lanayru Field" or
		CurrentStage == "Beside Castle Town" or
		CurrentStage == "South Castle Town" or
		CurrentStage == "Upper Zora's River" or
		CurrentStage == "Zora's Domain" then
			Tracker:UiHint("ActivateTab", "Overworld")
			Tracker:UiHint("ActivateTab", "Lanayru")
			Tracker:UiHint("ActivateTab", CurrentStage)
			print("Changing Map to: "..CurrentStage)
		elseif CurrentStage == "Hyrule Field" then
			if CurrentRoom == 6 or CurrentRoom == 1 or CurrentRoom == 15 then
				Tracker:UiHint("ActivateTab", "Overworld")
				Tracker:UiHint("ActivateTab", "Faron")
				Tracker:UiHint("ActivateTab", "Faron Field")
				print("Changing Map to: Faron Field")
			elseif CurrentRoom == 3 or CurrentRoom == 4 or CurrentRoom == 2 then
				Tracker:UiHint("ActivateTab", "Overworld")
				Tracker:UiHint("ActivateTab", "Eldin")
				Tracker:UiHint("ActivateTab", "Kakariko Gorge")
				print("Changing Map to: Kakariko Gorge")
			elseif CurrentRoom == 0 or CurrentRoom == 7 or CurrentRoom == 5 then
				Tracker:UiHint("ActivateTab", "Overworld")
				Tracker:UiHint("ActivateTab", "Eldin")
				Tracker:UiHint("ActivateTab", "Eldin Field")
				print("Changing Map to: Eldin Field")
			elseif CurrentRoom == 10 or CurrentRoom == 11 or CurrentRoom == 9 then
				Tracker:UiHint("ActivateTab", "Overworld")
				Tracker:UiHint("ActivateTab", "Lanayru")
				Tracker:UiHint("ActivateTab", "Lanayru Field")
				print("Changing Map to: Lanayru Field")
			elseif CurrentRoom == 13 or CurrentRoom == 14 or CurrentRoom == 12 then
				Tracker:UiHint("ActivateTab", "Overworld")
				Tracker:UiHint("ActivateTab", "Lanayru")
				Tracker:UiHint("ActivateTab", "Lake Hylia")
				print("Changing Map to: Lake Hylia")
			elseif CurrentRoom == 8 then
				Tracker:UiHint("ActivateTab", "Overworld")
				Tracker:UiHint("ActivateTab", "Lanayru")
				Tracker:UiHint("ActivateTab", "Beside Castle Town")
				print("Changing Map to: Beside Castle Town")
			elseif CurrentRoom == 16 then
				Tracker:UiHint("ActivateTab", "Overworld")
				Tracker:UiHint("ActivateTab", "Lanayru")
				Tracker:UiHint("ActivateTab", "South Castle Town")
				print("Changing Map to: South Castle Town")
			elseif CurrentRoom == 17 then
				Tracker:UiHint("ActivateTab", "Overworld")
				Tracker:UiHint("ActivateTab", "Castle Town")
				print("Changing Map to: Castle Town")
			end
		elseif CurrentStage == "Forest Temple" or
		CurrentStage == "Goron Mines" or
		CurrentStage == "Lakebed Temple" or
		CurrentStage == "Arbiter's Grounds" or
		CurrentStage == "Snowpeak Ruins" or
		CurrentStage == "Temple of Time" or
		CurrentStage == "City in the Sky" or
		CurrentStage == "Palace of Twilight" or
		CurrentStage == "Hyrule Castle" then
			if CurrentFloor == 0 then
				Tracker:UiHint("ActivateTab", "1F")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." 2F")
			elseif CurrentFloor == 1 then
				Tracker:UiHint("ActivateTab", "2F")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." 2F")
			elseif CurrentFloor == 2 then
				Tracker:UiHint("ActivateTab", "3F")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." 3F")
			elseif CurrentFloor == 3 then
				Tracker:UiHint("ActivateTab", "4F")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." 4F")
			elseif CurrentFloor == 4 then
				Tracker:UiHint("ActivateTab", "5F")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." 5F")
			elseif CurrentFloor == 5 then
				Tracker:UiHint("ActivateTab", "6F")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." 6F")
			elseif CurrentFloor == 6 then
				Tracker:UiHint("ActivateTab", "7F")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." 7F")
			elseif CurrentFloor == 7 then
				Tracker:UiHint("ActivateTab", "8F")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." 8F")
			elseif CurrentFloor == 255 then
				Tracker:UiHint("ActivateTab", "B1")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." B1")
			elseif CurrentFloor == 254 then
				Tracker:UiHint("ActivateTab", "B2")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." B2")
			elseif CurrentFloor == 253 then
				Tracker:UiHint("ActivateTab", "B3")
				Tracker:UiHint("ActivateTab", CurrentStage)
				print("Changing Map to: "..CurrentStage.." B3")
			end
		end
	end
end
Archipelago:AddClearHandler("clear handler", OnClear)
Archipelago:AddItemHandler("item handler", OnItem)
Archipelago:AddLocationHandler("location handler", OnLocation)
Archipelago:AddScoutHandler("scout handler", OnScout)
Archipelago:AddBouncedHandler("bounce handler", OnBounce)
Archipelago:AddSetReplyHandler("notify handler", OnNotify)
Archipelago:AddRetrievedHandler("notify launch handler", OnNotifyLaunch)