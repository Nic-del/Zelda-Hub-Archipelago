-- ITEM LOGIC
-- Check if player has at least 1 of following item
function has(item)
	if type(item) == "boolean" then return item end
	return Tracker:ProviderCountForCode(item) >= 1
end

-- Check if player has any of following items
function hasAny(items)
	for _, item in ipairs(items) do
		if type(item) == "table" then
			if hasAny(item) then return true end
		elseif has(item) then return true end
	end
	return false
end

-- Check if player has all following items
function hasAll(items)
	for _, item in ipairs(items) do
		if type(item) == "table" then
			if not hasAny(item) then return false end
		elseif not has(item) then
			return false
		end
	end
	return true
end

-- Check if player has at least X items
function hasAmount(item, amount)
	return Tracker:ProviderCountForCode(item) >= amount
end

-- Check if player has NONE of following items
function hasNone(items)
	for _, item in ipairs(items) do
		if has(item) then
			return false
		end
	end
	return true
end

-- Return number of item
function count(item)
	return Tracker:ProviderCountForCode(item)
end







-- HAS, CAN, GET
-- Return if has any damaging item
function hasDamagingItem()
	return hasAny({ "sword", "ballchain", "bow", hasBombs(), "boots", "shadowcrystal", "spinner" })
end

-- Check for bombbag
function hasBombs(...)
	if ... then return false end
	return hasAll({"bombbag", hasAny({canAccessEldin(), canAccessLanayru(true)})})
end

-- Check for water bombs
function hasWaterBombs()
	return hasAll({"waterbomb", hasBombs()})
end

-- Check if can smash
function canSmash(...)
	return hasAny({"ballchain", hasBombs(...)})
end

-- Check if webs can burn
function canBurnWebs()
	return hasAny({"lantern", hasBombs(), "ballchain"})
end

-- Check if has ranged weapon
function hasRangedItem()
	return hasAny({"ballchain", "slingshot", "bow", "clawshot", "boomerang"})
end

-- Check if bottled fairy can be used / used for single bonk do damage + one hit KO
function canUseBottledFairy()
	return has("bottle")
end

-- Check if bottled fairies can be used / used for ordon shield if bonk do damage + one hit KO
function canUseBottledFairies()
	return hasAmount("bottle", 2)
end

-- Check if bombs can be launched
function canLaunchBombs()
	return hasAll({hasAny({"bow", "boomerang"}), hasBombs()})
end

-- Check for bomb arrows
function canBombArrow()
	return hasAll({"bow", hasBombs()})
end

-- Check for cut webs
function canCutHangingWeb()
	return hasAny({"clawshot", "boomerang", "ballchain", hasAll({"bow", canGetArrows()})})
end
function canCutHangingWebGlitched()
	return hasAny({canCutHangingWeb(), hasAll({"bow", canGetArrowsGlitched()})})
end

-- Check if paintings can be knocked down
function canKnockDownHCPainting()
	return has("bow")
end
function canKnockDownHCPaintingGlitched()
	return hasAny({canKnockDownHCPainting(), hasAll({hasAny({hasBombs(), hasAll({"sword", hasAmount("hiddenskill", 6)})})}), hasAny({hasAll({"sword", canDoMoonBoots()}), canDoBSMoonBoots()})})
end

-- Check if monkey cage can be broken
function canBreakMonkeyCage()
	return hasAny({"sword", "ballchain", "boots", hasBombs(), "clawshot", "shadowcrystal", "spinner", hasAll({"bow", canGetArrows()})})
end
function canBreakMonkeyCageGlitched()
	return hasAny({canBreakMonkeyCage(), hasAll({"bow", canGetArrowsGlitched()}), hasAmount("hiddenskill", 2)})
end

-- Check if all monkey can be freed
function canFreeAllMonkeys()
	return hasAll({canBreakMonkeyCage(), hasAny({"lantern", hasAll({"skkeysy", hasAny({hasBombs(), "boots"})})}), canBurnWebs(), "boomerang", canDefeatBokoblin(), hasAny({hasAmount("ftsmallkey", 4), "skkeysy"})})
end
function canFreeAllMonkeysGlitched()
	return hasAll({canBreakMonkeyCageGlitched(), hasAny({"lantern", hasAll({"skkeysy", hasAny({hasBombs(), "boots"})})}), canBurnWebs(), "boomerang", canDefeatBokoblinGlitched(), hasAny({hasAmount("ftsmallkey", 4), "skkeysy"})})
end

-- Check if buttons can be pressed (GM)
function canPressMinesSwitch()
	return has("boots")
end
function canPressMinesSwitchGlitched()
	return hasAny({canPressMinesSwitch(), "ballchain"})
end

-- Check if hanging Baba can be knocked
function canKnockDownHangingBaba()
	return hasAny({"bow", "boomerang", "clawshot", "slingshot"})
end

-- Check if wooden doors can be broken
function canBreakWoodenDoor()
	return hasAny({"shadowcrystal", "sword", canSmash()})
end
function canBreakWoodenDoorGlitched()
	return hasAny({canBreakWoodenDoor(), canUseBacksliceAsSword()})
end





-- GLITCHED
function hasSwordorBS()
	return hasAny({"sword", hasAmount("hiddenskill", 3)})
end

function hasBottle()
	return hasAll({"bottle", "lantern"})
end

function hasBottles()
	return hasAll({hasAmount("bottle", 2), "lantern"})
end

function hasHeavyMod()
	return hasAny({"boots", "magicarmor"})
end

function hasCutsceneItem()
	return hasAny({"skybook", hasBottle(), "horsecall"})
end

function canDoLJA()
	return hasAll({"sword", "boomerang"})
end

function canDoJSLJA()
	return hasAll({"sword", "boomerang", hasAmount("hiddenskill", 6)})
end

function canDoMapGlitch()
	return hasAll({"shadowcrystal", canAccessEldin()})
end

function canDoStorage()
	return hasAll({canDoMapGlitch(), hasOneHandedItem()})
end

function hasOneHandedItem()
	return hasAny({"sword", hasBottle(), "boomerang", "clawshot", "lantern", "bow", "slingshot", "dominionrod"})
end

function canDoNicheStuff()
	return true
end

function canUseBacksliceAsSword()
	return hasAll({hasAmount("hiddenskill", 3)})
end

function canDoAirRefill()
	return hasAll({hasWaterBombs(), hasAny({"magicarmor", hasAll({"boots", getItemWheelSlotCount() >= 3})})})
end

function getItemWheelSlotCount()
	count = 0
	if has("clawshot") then count = count + 1 end
	if has("dominionrod") then count = count + 1 end
	if has("ballchain") then count = count + 1 end
	if has("spinner") then count = count + 1 end
	if has("bow") then count = count + 1 end
	if has("boots") then count = count + 1 end
	if has("boomerang") then count = count + 1 end
	if has("lantern") then count = count + 1 end
	if has("slingshot") then count = count + 1 end
	if has("fishingrod") then count = count + 1 end
	if has("hawkeye") then count = count + 1 end
	if has("bombbag") then count = count + 1 end
	if hasAmount("bombbag", 2) then count = count + 1 end
	if hasAmount("bombbag", 3) then count = count + 1 end
	if has("bottle") then count = count + 1 end
	if hasAmount("bottle", 2) then count = count + 1 end
	if hasAmount("bottle", 3) then count = count + 1 end
	if hasAmount("bottle", 4) then count = count + 1 end
	if has("aurusmemo") then count = count + 1 end
	if has("renadosletter") then count = count + 1 end
	if has("horsecall") then count = count + 1 end
	return count
end

function canDoMoonBoots()
	return hasAll({"sword", hasAny({"magicarmor", hasAll({"boots", getItemWheelSlotCount() >= 3})})})
end

function canDoJSMoonBoots()
	return hasAll({canDoMoonBoots(), hasAmount("hiddenskill", 6)})
end

function canDoBSMoonBoots()
	return hasAll({hasAmount("hiddenskill", 3), "magicarmor"})
end

function canDoEBMoonBoots()
	return hasAll({canDoMoonBoots(), "hiddenskill", "ordonsword"})
end

function canDoHSMoonBoots()
	return hasAll({canDoMoonBoots(), hasAmount("hiddenskill", 4), "sword", "shield"})
end

function canDoFlyGlitch()
	return hasAll({"fishingrod", hasHeavyMod()})
end

function canDoHiddenVillageGlitched()
	return hasAny({"bow", "ballchain", hasAll({"slingshot", hasAny({"shadowcrystal", "sword", hasBombs(), "boots", "spinner"})})})
end

function canDoFTWindlessBridgeRoom()
	return hasAny({hasBombs(), canDoBSMoonBoots(), canDoJSMoonBoots()})
end

function canClearForestGlitched()
	return hasAll({canCompletePrologue(), hasAny({"faronwoodsopen", "ftcompleted", canDoLJA(), canDoMapGlitch()})})
end

function canSkipKeyToDekuToad()
	return hasAny({"skkeysy", hasAmount("hiddenskill", 3), canDoBSMoonBoots(), canDoJSMoonBoots(), canDoLJA(), hasAll({hasBombs(), hasAny({hasHeavyMod(), hasAmount("hiddenskill", 6)})})})
end





--AREAS
function canCompletePrologue()
	return hasAny({hasAll({"sword", "slingshot", hasAny({"fwkey", "skkeysy"})}), "skipprologueon"})
end

function canClearForest()
	return hasAll({hasAny({"ftcompleted", "faronwoodsopen"}), canCompletePrologue(), faronTwilightCleared()})
end

function canCompleteMDH()
	return hasAny({"ltcompleted", "skipmdhon"})
end

function faronTwilightCleared()
	return hasAny({"faronvesseloflight", "farontwilightclearedon"})
end

function eldinTwilightCleared()
	return hasAny({"eldinvesseloflight", "eldintwilightclearedon"})
end

function lanayruTwilightCleared()
	return hasAny({"lanayruvesseloflight", "lanayrutwilightclearedon"})
end

function allTwilightCleared()
	return hasAll({faronTwilightCleared(), eldinTwilightCleared(), lanayruTwilightCleared()})
end

function hasCompletedAllDungeons()
	return hasAll({"ftcompleted", "gmcompleted", "ltcompleted", "agcompleted", "srcompleted", "ttcompleted", "cscompleted", "ptcompleted"})
end

function canGetArrows()
	return hasAny({canClearForest(), "shadowcrystal"})
end
function canGetArrowsGlitched()
	return hasAny({canGetArrows(), hasAll({"lantern", "bombbag", canDoLJA()})})
end

function canAccessEldin()
	return hasAny({canClearForest(), hasAll({"shadowcrystal", "openmapon", hasAny({"eldintwilightclearedon", "lanayrutwilightclearedon", "skipsnowpeakentranceon"})})})
end

function canAccessLanayru(...)
	return hasAny({hasAll({"shadowcrystal", "openmapon", hasAny({"lanayrutwilightclearedon", "skipsnowpeakentranceon"})}), hasAll({hasAny({canClearForest(), hasAll({"shadowcrystal", "openmapon", "eldintwilightclearedon"})}), hasAny({"gatekeys", "skkeysy", "glitcheson", canSmash(...)})})})
end





-- ENEMIES
function canDefeatAeralfos()
	return hasAll({"clawshot", hasAny({"sword", "ballchain", "shadowcrystal"})})
end
function canDefeatAeralfosGlitched()
	return hasAll({"clawshot", hasAny({"boots", canDefeatAeralfos()})})
end

function canDefeatArmos()
	return hasAny({"sword", "ballchain", "bow", "shadowcrystal", "clawshot", hasBombs(), "spinner"})
end
function canDefeatArmosGlitched()
	return hasAny({canDefeatArmos(), "boots", canUseBacksliceAsSword()})
end

function canDefeatBabaSerpent()
	return hasAny({"sword", "ballchain", "bow", hasAll({canDoNicheStuff(), "boots"}), "spinner", "shadowcrystal", hasBombs(), canUseBacksliceAsSword()})
end
function canDefeatBabaSerpentGlitched()
	return hasAny({canDefeatBabaSerpent(), "boots", canUseBacksliceAsSword()})
end

function canDefeatBabyGohma()
	return hasAny({"sword", "ballchain", "spinner", "slingshot", "clawshot", hasBombs()})
end
function canDefeatBabyGohmaGlitched()
	return hasAny({canDefeatBabyGohma(), "boots", canUseBacksliceAsSword()})
end

function canDefeatBari()
	return hasAny({hasWaterBombs(), "clawshot"})
end

function canDefeatBeamos()
	return hasAny({"ballchain", "bow", hasBombs()})
end

function canDefeatBigBaba()
	return hasAny({"sword", "ballchain", hasAll({"bow", canGetArrows()}), "shadowcrystal", "spinner", hasBombs(), })
end
function canDefeatBigBabaGlitched()
	return hasAny({canDefeatBigBaba(), hasAll({"bow", canGetArrowsGlitched()}), "boots", canUseBacksliceAsSword()})
end

function canDefeatBokoblin()
	return hasAny({"sword", "ballchain", hasAll({"bow", canGetArrows()}), "spinner", "slingshot", "shadowcrystal", hasBombs()})
end
function canDefeatBokoblinGlitched()
	return hasAny({canDefeatBokoblin(), hasAll({"bow", canGetArrowsGlitched()}), "boots", canUseBacksliceAsSword()})
end

function canDefeatBokoblinRed()
	return hasAny({"sword", "ballchain", hasAll({"bow", canGetArrows()}), "shadowcrystal", hasBombs()})
end
function canDefeatBokoblinRedGlitched()
	return hasAny({canDefeatBokoblinRed(), hasAll({"bow", canGetArrowsGlitched()}), canUseBacksliceAsSword()})
end

function canDefeatBombfish()
	return hasAll({"boots", hasAny({"sword", "clawshot", hasAll({"shield", hasAmount("hiddenskill", 2)})})})
end
function canDefeatBombfishGlitched()
	return hasAny({canDefeatBombfish(), hasAll({"magicarmor", hasAny({"sword", "clawshot", hasAll({"shield", hasAmount("hiddenskill", 2)})})})})
end

function canDefeatBombling()
	return hasAny({"sword", "ballchain", hasAll({"bow", canGetArrows()}), "spinner", "shadowcrystal", "clawshot"})
end
function canDefeatBomblingGlitched()
	return hasAny({canDefeatBombling(), hasAll({"bow", canGetArrowsGlitched()}), "boots"})
end

function canDefeatBomskit()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatBomskitGlitched()
	return hasAny({canDefeatBomskit(), canUseBacksliceAsSword(), "boots"})
end

function canDefeatBubble()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal"})
end
function canDefeatBubbleGlitched()
	return hasAny({canDefeatBubble(), "boots", canUseBacksliceAsSword()})
end

function canDefeatBulblin()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatBulblinGlitched()
	return hasAny({canDefeatBulblin(), "boots", canUseBacksliceAsSword()})
end

function canDefeatChilfos()
	return hasAny({"sword", "ballchain", "shadowcrystal", "spinner", hasBombs()})
end
function canDefeatChilfosGlitched()
	return hasAny({canDefeatChilfos(), "boots", canUseBacksliceAsSword()})
end

function canDefeatChu()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", "clawshot", hasBombs()})
end
function canDefeatChuGlitched()
	return hasAny({canDefeatChu(), "boots", canUseBacksliceAsSword()})
end

function canDefeatChuWorm()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal"})
end
function canDefeatChuWormGlitched()
	return hasAny({canDefeatChuWorm(), "boots", canUseBacksliceAsSword()})
end

function canDefeatDarknut()
	return has("sword")
end

function canDefeatDekuBaba()
	return hasAny({"sword", "ballchain", "bow", "spinner", hasAmount("hiddenskill", 2), "slingshot", "clawshot", hasBombs()})
end
function canDefeatDekuBabaGlitched()
	return hasAny({canDefeatDekuBaba(), "boots", canUseBacksliceAsSword()})
end

function canDefeatDekuLike()
	return hasBombs()
end

function canDefeatDodongo()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatDodongoGlitched()
	return hasAny({canDefeatDodongo(), "boots", canUseBacksliceAsSword()})
end

function canDefeatDinalfos()
	return hasAny({"sword", "ballchain", "shadowcrystal"})
end

function canDefeatFireBubble()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal"})
end
function canDefeatFireBubbleGlitched()
	return hasAny({canDefeatFireBubble(), "boots", canUseBacksliceAsSword()})
end

function canDefeatFireKeese()
	return hasAny({"sword", "ballchain", "bow", "spinner", "slingshot", "shadowcrystal"})
end
function canDefeatFireKeeseGlitched()
	return hasAny({canDefeatFireKeese(), "boots", canUseBacksliceAsSword()})
end

function canDefeatFireToadpoli()
	return hasAny({"sword", "ballchain", "bow", hasAll({hasAmount("hiddenskill", 2), "hylianshield"})})
end

function canDefeatFreezard()
	return has("ballchain")
end

function canDefeatGoron()
	return hasAny({"sword", "ballchain", "bow", "spinner", hasAll({hasAmount("hiddenskill", 2), "shield"}), "slingshot", "clawshot", hasBombs()})
end
function canDefeatGoronGlitched()
	return hasAny({canDefeatGoron(), "boots", canUseBacksliceAsSword()})
end

function canDefeatGhoulRat()
	return has("shadowcrystal")
end

function canDefeatGuay()
	return hasAny({"sword", "ballchain", "bow", "shadowcrystal", "slingshot"})
end
function canDefeatGuayGlitched()
	return hasAny({canDefeatGuay(), "boots"})
end

function canDefeatHelmasaur()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatHelmasaurGlitched()
	return hasAny({canDefeatHelmasaur(), "boots", canUseBacksliceAsSword()})
end

function canDefeatHelmasaurus()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatHelmasaurusGlitched()
	return hasAny({canDefeatHelmasaurus(), "boots", canUseBacksliceAsSword()})
end

function canDefeatIceBubble()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal"})
end
function canDefeatIceBubbleGlitched()
	return hasAny({canDefeatIceBubble(), "boots", canUseBacksliceAsSword()})
end

function canDefeatIceKeese()
	return hasAny({"sword", "ballchain", "bow", "spinner", "slingshot", "shadowcrystal"})
end
function canDefeatIceKeeseGlitched()
	return hasAny({canDefeatIceKeese(), "boots", canUseBacksliceAsSword()})
end

function canDefeatPoe()
	return has("shadowcrystal")
end

function canDefeatKargorok()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal"})
end
function canDefeatKargorokGlitched()
	return hasAny({canDefeatKargorok(), "boots", canUseBacksliceAsSword()})
end

function canDefeatKeese()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal"})
end
function canDefeatKeeseGlitched()
	return hasAny({canDefeatKeese(), "boots", canUseBacksliceAsSword()})
end

function canDefeatLeever()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatLeeverGlitched()
	return hasAny({canDefeatLeever(), "boots"})
end

function canDefeatLizalfos()
	return hasAny({"sword", "ballchain", "bow", "shadowcrystal", hasBombs()})
end
function canDefeatLizalfosGlitched()
	return hasAny({canDefeatLizalfos(), "boots", canUseBacksliceAsSword()})
end

function canDefeatMiniFreezard()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatMiniFreezardGlitched()
	return hasAny({canDefeatMiniFreezard(), "boots", canUseBacksliceAsSword()})
end

function canDefeatMoldorm()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatMoldormGlitched()
	return hasAny({canDefeatMoldorm(), "boots"})
end

function canDefeatPoisonMite()
	return hasAny({"sword", "ballchain", "bow", "lantern", "spinner", "shadowcrystal"})
end

function  canDefeatPuppet()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function  canDefeatPuppetGlitched()
	return hasAny({canDefeatPuppet(), "boots", canUseBacksliceAsSword()})
end

function canDefeatRat()
	return hasAny({"sword", "ballchain", "bow", "spinner", "slingshot", "shadowcrystal", hasBombs()})
end
function canDefeatRatGlitched()
	return hasAny({canDefeatRat(), "boots", canUseBacksliceAsSword()})
end

function canDefeatRedeadKnight()
	return hasAny({"sword", "ballchain", "bow", "shadowcrystal", hasBombs()})
end
function canDefeatRedeadKnightGlitched()
	return hasAny({canDefeatRedeadKnight(), "boots", canUseBacksliceAsSword()})
end

function canDefeatShadowBeast()
	return hasAny({"sword", hasAll({"shadowcrystal", canCompleteMDH()})})
end

function canDefeatShadowBulblin()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatShadowBulblinGlitched()
	return hasAny({canDefeatShadowBulblin(), "boots", canUseBacksliceAsSword()})
end

function canDefeatShadowDekuBaba()
	return hasAny({"sword", "ballchain", "bow", "spinner", hasAmount("hiddenskill", 2), "slingshot", "clawshot", hasBombs()})
end
function canDefeatShadowDekuBabaGlitched()
	return hasAny({canDefeatShadowDekuBaba(), "boots", canUseBacksliceAsSword()})
end

function canDefeatShadowInsect()
	return has("shadowcrystal")
end

function canDefeatShadowKargorok()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatShadowKargorokGlitched()
	return hasAny({canDefeatShadowKargorok(), "boots", canUseBacksliceAsSword()})
end

function canDefeatShadowKeese()
	return hasAny({"sword", "ballchain", "bow", "spinner", "slingshot", "shadowcrystal"})
end
function canDefeatShadowKeeseGlitched()
	return hasAny({canDefeatShadowKeese(), "boots", canUseBacksliceAsSword()})
end

function canDefeatShadowVermin()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatShadowVerminGlitched()
	return hasAny({canDefeatShadowVermin(), "boots", canUseBacksliceAsSword()})
end

function canDefeatShellBlade()
	return hasAny({hasWaterBombs(), hasAll({"sword", "boots"})})
end
function canDefeatShellBladeGlitched()
	return hasAny({canDefeatShellBlade(), hasAll({"sword", "magicarmor"})})
end

function canDefeatSkullFish()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal"})
end
function canDefeatSkullFishGlitched()
	return hasAny({canDefeatSkullFish(), "boots"})
end

function canDefeatSkulltula()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatSkulltulaGlitched()
	return hasAny({canDefeatSkulltula(), "boots", canUseBacksliceAsSword()})
end

function canDefeatStalfos()
	return canSmash()
end

function canDefeatStalhound()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatStalhoundGlitched()
	return hasAny({canDefeatStalhound(), "boots", canUseBacksliceAsSword()})
end

function canDefeatStalchild()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatStalchildGlitched()
	return hasAny({canDefeatStalchild(), "boots", canUseBacksliceAsSword()})
end

function canDefeatTektite()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatTektiteGlitched()
	return hasAny({canDefeatTektite(), "boots", canUseBacksliceAsSword()})
end

function canDefeatTileWorm()
	return hasAll({hasAny({"sword", "ballchain", "bow", "shadowcrystal", "spinner", hasBombs()}), "boomerang"})
end
function canDefeatTileWormGlitched()
	return hasAny({canDefeatTileWorm(), hasAll({hasAny({"boots", canUseBacksliceAsSword()}), "boomerang"})})
end

function canDefeatToado()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal"})
end

function canDefeatWaterToadpoli()
	return hasAny({"sword", "ballchain", "bow", hasAll({hasAmount("hiddenskill", 2), "shield"})})
end

function canDefeatTorchSlug()
	return hasAny({"sword", "ballchain", "bow", "shadowcrystal", hasBombs()})
end

function canDefeatWalltula()
	return hasAny({"ballchain", "slingshot", hasAll({"bow", canGetArrows()}), "boomerang", "clawshot"})
end
function canDefeatWalltulaGlitched()
	return hasAny({canDefeatWalltula(), hasAll({"bow", canGetArrowsGlitched()})})
end

function canDefeatWhiteWolfos()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatWhiteWolfosGlitched()
	return hasAny({canDefeatWhiteWolfos(), "boots"})
end

function canDefeatYoungGohma()
	return hasAny({"sword", "ballchain", "bow", "spinner", "shadowcrystal", hasBombs()})
end
function canDefeatYoungGohmaGlitched()
	return hasAny({canDefeatYoungGohma(), "boots"})
end

function canDefeatZantHead()
	return hasAny({"shadowcrystal", "sword"})
end
function canDefeatZantHeadGlitched()
	return hasAny({canDefeatZantHead(), canUseBacksliceAsSword()})
end

function canDefeatOok()
	return hasAny({"sword", "ballchain", hasAll({"bow", canGetArrows()}), "shadowcrystal", hasBombs()})
end
function canDefeatOokGlitched()
	return hasAny({canDefeatOok(), hasAll({"bow", canGetArrowsGlitched()}), "boots", canUseBacksliceAsSword()})
end

function canDefeatDangoro()
	return hasAll({hasAny({"sword", "shadowcrystal", hasAll({"bow", hasBombs()})}), "boots"})
end
function canDefeatDangoroGlitched()
	return hasAny({canDefeatDangoro(), hasAll({"ballchain", "boots"})})
end

function canDefeatCarrierKargorok()
	return has("shadowcrystal")
end

function canDefeatTwilitBloat()
	return has("shadowcrystal")
end

function canDefeatDekuToad()
	return hasAny({"sword", "ballchain", "bow", "shadowcrystal", hasBombs()})
end
function canDefeatDekuToadGlitched()
	return hasAny({canDefeatDekuToad(), "boots", canUseBacksliceAsSword()})
end

function canDefeatSkullKid()
	return has("bow")
end

function canDefeatKingBulblinBridge()
	return has("bow")
end

function canDefeatKingBulblinDesert()
	return hasAny({"sword", "ballchain", "shadowcrystal", "largequiver"})
end
function canDefeatKingBulblinDesertGlitched()
	return hasAny({canDefeatKingBulblinDesert(), canUseBacksliceAsSword()})
end

function canDefeatKingBulblinCastle()
	return hasAny({"sword", "ballchain", "shadowcrystal", "largequiver"})
end

function canDefeatDeathSword()
	return hasAll({"sword", hasAny({"boomerang", "bow", "clawshot"}), "shadowcrystal"})
end

function canDefeatDarkhammer()
	return hasAny({"sword", "ballchain", "bow", "shadowcrystal", hasBombs()})
end
function canDefeatDarkhammerGlitched()
	return hasAny({canDefeatDarkhammer(), "boots"})
end

function canDefeatPhantomZant()
	return hasAny({"shadowcrystal", "sword"})
end

function canDefeatDiababa()
	return hasAny({canLaunchBombs(), hasAll({"boomerang", hasAny({"sword", "ballchain", "shadowcrystal", hasBombs()})})})
end
function canDefeatDiababaGlitched()
	return hasAny({canDefeatDiababa(), hasAll({"boomerang", "boots"})})
end

function canDefeatFyrus()
	return hasAll({"bow", "boots", "sword"})
end

function canDefeatMorpheel()
	return hasAll({"zoraarmor", "boots", "sword", "clawshot"})
end
function canDefeatMorpheelGlitched()
	return hasAny({canDefeatMorpheel(), hasAll({"clawshot", canDoAirRefill(), "sword"})})
end

function canDefeatStallord()
	return hasAll({"spinner", "sword"})
end

function canDefeatBlizzeta()
	return has("ballchain")
end

function canDefeatArmogohma()
	return hasAll({"bow", "dominionrod"})
end

function canDefeatArgorok()
	return hasAll({"doubleclawshot", "ordonsword", "boots"})
end
function canDefeatArgorokGlitched()
	return hasAny({canDefeatArgorok(), hasAll({"doubleclawshot", "ordonsword", "magicarmor"})})
end

function canDefeatZant()
	return hasAll({"mastersword", "boomerang", "clawshot", "ballchain", "boots", "zoraarmor"})
end
function canDefeatZantGlitched()
	return hasAny({canDefeatZant(), hasAll({"mastersword", "boomerang", "clawshot", "ballchain", "magicarmor", canDoAirRefill()})})
end

function canDefeatGanondorf()
	return hasAll({"shadowcrystal", "mastersword", "hiddenskill"})
end