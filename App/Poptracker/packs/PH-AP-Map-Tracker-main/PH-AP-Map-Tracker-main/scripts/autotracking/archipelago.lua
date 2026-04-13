
--require("scripts/autotracking/slots_data_mapping")
require("scripts/autotracking/item_mapping")
require("scripts/autotracking/location_mapping")
--require("scripts/autotracking/hints_mapping")

CUR_INDEX = -1
--SLOT_DATA = nil
SLOT_DATA = {}

function has_value (t, val)
    for i, v in ipairs(t) do
        if v == val then return 1 end
    end
    return 0
end

function dump(o, depth)
    if depth == nil then
        depth = 0
    end
    if type(o) == 'table' then
        local tabs = ('\t'):rep(depth)
        local tabs2 = ('\t'):rep(depth + 1)
        local s = '{'
        for k, v in pairs(o) do
            if type(k) ~= 'number' then
                k = '"' .. k .. '"'
            end
            s = s .. tabs2 .. '[' .. k .. '] = ' .. dump(v, depth + 1) .. ','
        end
        return s .. tabs .. '}'
    else
        return tostring(o)
    end
end

function forceUpdate()
    local update = Tracker:FindObjectForCode("update")
    update.Active = not update.Active
end

function onClearHandler(slot_data)
    local clear_timer = os.clock()
    
    ScriptHost:RemoveWatchForCode("StateChange")
    -- Disable tracker updates.
    Tracker.BulkUpdate = true
    -- Use a protected call so that tracker updates always get enabled again, even if an error occurred.
    local ok, err = pcall(onClear, slot_data)
    -- Enable tracker updates again.
    if ok then
        -- Defer re-enabling tracker updates until the next frame, which doesn't happen until all received items/cleared
        -- locations from AP have been processed.
        local handlerName = "AP onClearHandler"
        local function frameCallback()
            ScriptHost:AddWatchForCode("StateChange", "*", StateChange)
            ScriptHost:RemoveOnFrameHandler(handlerName)
            Tracker.BulkUpdate = false
            forceUpdate()
            print(string.format("Time taken total: %.2f", os.clock() - clear_timer))
        end
        ScriptHost:AddOnFrameHandler(handlerName, frameCallback)
    else
        Tracker.BulkUpdate = false
        print("Error: onClear failed:")
        print(err)
    end
end

function onClear(slot_data)
    print(string.format("called OnClear, slot_data:\n%s", dump(slot_data)))
	PLAYER_ID = Archipelago.PlayerNumber or -1
    TEAM_NUMBER = Archipelago.TeamNumber or 0
    print(PLAYER_ID, TEAM_NUMBER)
	SLOT_DATA = slot_data
    CUR_INDEX = -1
    -- reset locations
    for _, location_array in pairs(LOCATION_MAPPING) do
        for _, location in pairs(location_array) do
            if location then
                local obj = Tracker:FindObjectForCode(location[1])
                if obj then
                    if location[1]:sub(1, 1) == "@" then
                        obj.AvailableChestCount = obj.ChestCount
                    else
                        obj.Active = false
                    end
                end
            end
        end
    end
    -- reset items
    for _, item_pair in pairs(ITEM_MAPPING) do
		item_code = item_pair[1]
		item_type = item_pair[2]
        if item_code and item_type then
            local obj = Tracker:FindObjectForCode(item_code)
            if obj then
                if item_type == "toggle" then
                    obj.Active = false
                elseif item_type == "progressive" then
                    obj.CurrentStage = 0
                    obj.Active = false
                elseif item_type == "consumable" then
                    if obj.MinCount then
                        obj.AcquiredCount = obj.MinCount
                    else
                        obj.AcquiredCount = 0
                    end
                elseif item_type == "progressive_toggle" then
                    obj.CurrentStage = 0
                    obj.Active = false
                end
            end
        end
    end
    -- reset settings
	Tracker:FindObjectForCode("gem_packs").AcquiredCount = slot_data["spirit_gem_packs"]
	if slot_data["randomize_salvage"] == 1 then
		Tracker:FindObjectForCode("salvage_setting").Active = true
	end
	if slot_data["randomize_fishing"] == 1 then
		Tracker:FindObjectForCode("fishing_setting").Active = true
	end
	if slot_data["randomize_triforce_crest"] == 0 then
		Tracker:FindObjectForCode("triforcecrest").Active = true
	end
	if slot_data["randomize_frogs"] == 1 then
		Tracker:FindObjectForCode("warpx").Active = true
		Tracker:FindObjectForCode("warpphi").Active = true
		Tracker:FindObjectForCode("warpn").Active = true
		Tracker:FindObjectForCode("warpomega").Active = true
		Tracker:FindObjectForCode("warpw").Active = true
		Tracker:FindObjectForCode("warpsquare").Active = true
	end
	
	if Archipelago.PlayerNumber > -1 then

        HINTS_ID = "_read_hints_"..TEAM_NUMBER.."_"..PLAYER_ID
        Archipelago:SetNotify({HINTS_ID})
        Archipelago:Get({HINTS_ID})
    end
end

function onItem(index, item_id, item_name, player_number)
    if index <= CUR_INDEX then
        return
    end
    local is_local = player_number == Archipelago.PlayerNumber
    CUR_INDEX = index;
    local item = ITEM_MAPPING[item_id]
    if not item or not item[1] then
        --print(string.format("onItem: could not find item mapping for id %s", item_id))
        return
    end
    for _, item_pair in pairs(item) do
        item_code = item_pair[1]
        item_type = item_pair[2]
        local obj = Tracker:FindObjectForCode(item_code)
        if obj then
            if item_type == "toggle" then
                -- print("toggle")
                obj.Active = true
            elseif item_type == "progressive" then
                -- print("progressive")
                if obj.Active then
                    obj.CurrentStage = obj.CurrentStage + 1
                else
                    obj.Active = true
                end
            elseif item_type == "consumable" then
                -- print("consumable")
                obj.AcquiredCount = obj.AcquiredCount + obj.Increment * (tonumber(item_pair[3]) or 1)
            elseif item_type == "progressive_toggle" then
                -- print("progressive_toggle")
                if obj.Active then
                    obj.CurrentStage = obj.CurrentStage + 1
                else
                    obj.Active = true
                end
            end
        else
            print(string.format("onItem: could not find object for code %s", item_code[1]))
        end
    end
end

--called when a location gets cleared
function onLocation(location_id, location_name)
    local location_array = LOCATION_MAPPING[location_id]
    if not location_array or not location_array[1] then
        print(string.format("onLocation: could not find location mapping for id %s", location_id))
        return
    end

    for _, location in pairs(location_array) do
        local obj = Tracker:FindObjectForCode(location[1])
        -- print(location, obj)
        if obj then
            if location[1]:sub(1, 1) == "@" then
                obj.AvailableChestCount = obj.AvailableChestCount - 1
            else
                obj.Active = true
            end
        else
            print(string.format("onLocation: could not find location_object for code %s", location[1]))
        end
    end
end

function onEvent(key, value, old_value)
    updateEvents(value)
end

function onEventsLaunch(key, value)
    updateEvents(value)
end

-- this Autofill function is meant as an example on how to do the reading from slotdata and mapping the values to 
-- your own settings
-- function autoFill()
--     if SLOT_DATA == nil  then
--         print("its fucked")
--         return
--     end
--     -- print(dump_table(SLOT_DATA))

--     mapToggle={[0]=0,[1]=1,[2]=1,[3]=1,[4]=1}
--     mapToggleReverse={[0]=1,[1]=0,[2]=0,[3]=0,[4]=0}
--     mapTripleReverse={[0]=2,[1]=1,[2]=0}

--     slotCodes = {
--         map_name = {code="", mapping=mapToggle...}
--     }
--     -- print(dump_table(SLOT_DATA))
--     -- print(Tracker:FindObjectForCode("autofill_settings").Active)
--     if Tracker:FindObjectForCode("autofill_settings").Active == true then
--         for settings_name , settings_value in pairs(SLOT_DATA) do
--             -- print(k, v)
--             if slotCodes[settings_name] then
--                 item = Tracker:FindObjectForCode(slotCodes[settings_name].code)
--                 if item.Type == "toggle" then
--                     item.Active = slotCodes[settings_name].mapping[settings_value]
--                 else 
--                     -- print(k,v,Tracker:FindObjectForCode(slotCodes[k].code).CurrentStage, slotCodes[k].mapping[v])
--                     item.CurrentStage = slotCodes[settings_name].mapping[settings_value]
--                 end
--             end
--         end
--     end
-- end

function onNotify(key, value, old_value)
    print("onNotify", key, value, old_value)
    if value ~= old_value and key == HINTS_ID then
        for _, hint in ipairs(value) do
            if hint.finding_player == Archipelago.PlayerNumber then
                if hint.found then
                    updateHints(hint.location, true)
                else
                    updateHints(hint.location, false)
                end
            end
        end
    end
end

function onNotifyLaunch(key, value)
    print("onNotifyLaunch", key, value)
    if key == HINTS_ID then
        for _, hint in ipairs(value) do
            -- print("hint", hint, hint.found)
            -- print(dump_table(hint))
            if hint.finding_player == Archipelago.PlayerNumber then
                if hint.found then
                    updateHints(hint.location, true)
                else
                    updateHints(hint.location, false)
                end
            end
        end
    end
end

function updateHints(locationID, clear)
    local item_codes = HINTS_MAPPING[locationID]

    for _, item_table in ipairs(item_codes, clear) do
        for _, item_code in ipairs(item_table) do
            local obj = Tracker:FindObjectForCode(item_code)
            if obj then
                if not clear then
                    obj.Active = true
                else
                    obj.Active = false
                end
            else
                print(string.format("No object found for code: %s", item_code))
            end
        end
    end
end


-- ScriptHost:AddWatchForCode("settings autofill handler", "autofill_settings", autoFill)
Archipelago:AddClearHandler("clear handler", onClearHandler)
Archipelago:AddItemHandler("item handler", onItem)
Archipelago:AddLocationHandler("location handler", onLocation)

Archipelago:AddSetReplyHandler("notify handler", onNotify)
Archipelago:AddRetrievedHandler("notify launch handler", onNotifyLaunch)



--doc
--hint layout
-- {
--     ["receiving_player"] = 1,
--     ["class"] = Hint,
--     ["finding_player"] = 1,
--     ["location"] = 67361,
--     ["found"] = false,
--     ["item_flags"] = 2,
--     ["entrance"] = ,
--     ["item"] = 66062,
-- } 
