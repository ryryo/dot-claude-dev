on run argv
  set actionMode to "focus-only"
  if (count of argv) is greater than 0 then set actionMode to item 1 of argv
  if actionMode is not "focus-only" then error "Direct AppleScript prompt insertion is not supported for the current Cursor Agents accessibility tree; use mac-ide-cdp"

  tell application "Cursor" to activate
  delay 1

  tell application "System Events"
    if not (exists process "Cursor") then error "Cursor process is not available"
    tell process "Cursor"
      set frontmost to true

      if exists window "Cursor Agents" then
        tell window "Cursor Agents" to set focused to true
        return "Cursor Agents focused"
      end if

      error "Cursor Agents window was not found"
    end tell
  end tell
end run
