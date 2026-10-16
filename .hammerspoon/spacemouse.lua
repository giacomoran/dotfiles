-- Keep the SpaceMouse from moving the pointer while 3Dconnexion's driver is off.
--
-- Without 3DconnexionHelper, macOS's own HID driver treats the SpaceMouse
-- Compact as a pointer: pushing or tilting the cap moves the cursor, twisting it
-- scrolls, and pressing it down clicks. Chrome still reads its raw reports over
-- WebHID (the ai-saldatura operator UI jogs the robot with it), so the device
-- must stay open to everyone; this only undoes what macOS makes of it.
--
-- Every event carries the registry id of the HID service that sent it (CGEvent
-- field 87, the sender id), so the SpaceMouse's events are told apart from the
-- trackpad's and the mouse's. Deleting an event keeps it from applications (no
-- click, no scroll), but the window server has already moved the cursor by
-- then, so the cursor is also put back where the other devices left it: the
-- fix the Unity SpaceNavigator plugin settled on
-- (https://github.com/PatHightree/SpaceNavigator/issues/65).

local idVendor3Dconnexion = 0x256f
local idProductSpaceMouseCompact = 0xc635
local fieldSenderId = 87

local idsSenderSpaceMouse = {}

-- Where the trackpad and the mouse last put the cursor, which the SpaceMouse's
-- events are undone back to.
local positionHeld = hs.mouse.absolutePosition()

-- The registry ids of the SpaceMouse's HID services, as `hidutil list` shows
-- them under "Services:". They change when the device is plugged in again.
local function findIdsSenderSpaceMouse()
  local output = hs.execute(string.format(
    "/usr/bin/hidutil list --matching '{\"VendorID\":%d,\"ProductID\":%d}'",
    idVendor3Dconnexion,
    idProductSpaceMouseCompact
  ))
  local ids = {}
  local isInServices = false
  for line in output:gmatch("[^\n]+") do
    if line:match("^Services:") then
      isInServices = true
    elseif line:match("^Devices:") then
      isInServices = false
    elseif isInServices then
      local idRegistry = line:match("^%s*0x%x+%s+0x%x+%s+0x%x+%s+%d+%s+%d+%s+(0x%x+)")
      if idRegistry then
        ids[tonumber(idRegistry)] = true
      end
    end
  end
  return ids
end

local function refreshIdsSenderSpaceMouse()
  idsSenderSpaceMouse = findIdsSenderSpaceMouse()
  local count = 0
  for _ in pairs(idsSenderSpaceMouse) do
    count = count + 1
  end
  print(string.format("spacemouse: holding the pointer against %d HID service(s)", count))
end

local typesEvent = hs.eventtap.event.types
local tapPointer = hs.eventtap.new({
  typesEvent.mouseMoved,
  typesEvent.leftMouseDown,
  typesEvent.leftMouseUp,
  typesEvent.leftMouseDragged,
  typesEvent.rightMouseDown,
  typesEvent.rightMouseUp,
  typesEvent.rightMouseDragged,
  typesEvent.otherMouseDown,
  typesEvent.otherMouseUp,
  typesEvent.otherMouseDragged,
  typesEvent.scrollWheel,
}, function(event)
  -- Another device's event: remember where it left the cursor, and pass it on.
  if idsSenderSpaceMouse[event:getProperty(fieldSenderId)] ~= true then
    positionHeld = event:location()
    return false
  end

  -- The SpaceMouse's: put the cursor back, and delete the event so no
  -- application sees a move, a click or a scroll.
  hs.mouse.absolutePosition(positionHeld)
  return true
end)

-- Look the services up again whenever a SpaceMouse is plugged in or out; the
-- new service needs a moment to appear after the USB device does.
local watcherUsb = hs.usb.watcher.new(function(device)
  if device.vendorID == idVendor3Dconnexion then
    hs.timer.doAfter(1, refreshIdsSenderSpaceMouse)
  end
end)

refreshIdsSenderSpaceMouse()
tapPointer:start()
watcherUsb:start()

return { tapPointer = tapPointer, watcherUsb = watcherUsb }
