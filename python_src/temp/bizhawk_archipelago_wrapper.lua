
-- BizHawk Archipelago Wrapper (Dynamic Paths via Environment)
local hub_temp_dir = os.getenv("HUB_TEMP_DIR") or [[C:\Users\linksweld\Documents\zelda-multi-launcher-hub\python_src\temp]]
local shutdown_flag = hub_temp_dir .. "/oracleofages_shutdown.flag"

-- 1. Shutdown / Save / Load Listener
local save_flag = hub_temp_dir .. "/oracleofages_save.flag"
local load_flag = hub_temp_dir .. "/oracleofages_load.flag"
local pause_flag = hub_temp_dir .. "/oracleofages_pause.flag"
local resume_flag = hub_temp_dir .. "/oracleofages_resume.flag"

local function check_launcher_signals()
    local fs = io.open(save_flag, "r")
    if fs then
        local slot_str = fs:read("*a")
        fs:close()
        os.remove(save_flag)
        local prefix = os.getenv("HUB_GAME_PREFIX") or "bizhawk"
        local slot = tonumber(slot_str) or 10
        savestate.saveslot(slot)
        print("Launcher: Auto-saved (AP) to slot " .. slot .. " (" .. prefix .. ")")
    end

    local fl = io.open(load_flag, "r")
    if fl then
        local slot_str = fl:read("*a")
        fl:close()
        os.remove(load_flag)
        local prefix = os.getenv("HUB_GAME_PREFIX") or "bizhawk"
        local slot = tonumber(slot_str) or 10
        savestate.loadslot(slot)
        print("Launcher: Auto-loaded (AP) from slot " .. slot .. " (" .. prefix .. ")")
    end

    local f = io.open(shutdown_flag, "r")
    if f then
        f:close()
        os.remove(shutdown_flag)
        client.exit()
    end
    
    local fp = io.open(pause_flag, "r")
    if fp then
        fp:close()
        os.remove(pause_flag)
        client.pause()
    end

    local fr = io.open(resume_flag, "r")
    if fr then
        fr:close()
        os.remove(resume_flag)
        client.unpause()
    end
end

local frame_count = 0
local last_check = os.clock()

local function listener_logic()
    frame_count = frame_count + 1
    if frame_count < 5 then return end
    frame_count = 0
    check_launcher_signals()
    last_check = os.clock()
end

event.onframestart(listener_logic)

-- Robust registration with fallback
-- Onpaint runs even when paused (on UI redraw/focus)
-- Robust registration with fallback
if event.onpaint then
    event.onpaint(function()
        if client.ispaused() then check_launcher_signals() end
    end)
elseif gui and gui.register then
    gui.register(function()
        if client.ispaused() then check_launcher_signals() end
    end)
end

-- 2. Setup Paths for Archipelago
local arch_lua_dir = os.getenv("ARCH_LUA_DIR") or [[C:\ProgramData\Archipelago\data\lua]]
package.path = arch_lua_dir .. "\\?.lua;" .. package.path
package.cpath = arch_lua_dir .. "\\?.dll;" .. arch_lua_dir .. "\\x64\\?.dll;" .. arch_lua_dir .. "\\x86\\?.dll;" .. package.cpath

-- Mock io.popen('cd') car socket.lua l'utilise pour trouver ses DLLs
local old_popen = io.popen
io.popen = function(cmd, mode)
    if cmd == "cd" then
        return {
            read = function() return arch_lua_dir end,
            close = function() return true end
        }
    end
    if old_popen then return old_popen(cmd, mode) end
    return nil
end

-- 3. Launch Archipelago Script
print("BizHawk Boot Wrapper: Waiting for emulator to be ready (0.5s)...")
for i = 1, 30 do
    check_launcher_signals()
    emu.frameadvance()
end

print("Launching Archipelago Connector...")
-- Re-inject the listener check before dofile to ensure it's still active
dofile([[C:\ProgramData\Archipelago\data\lua\connector_bizhawk_generic.lua]])
