on run argv
  if (count of argv) is less than 1 then error "prompt file path is required"
  set promptFile to item 1 of argv
  set submitMode to "no-submit"
  if (count of argv) is greater than 1 then set submitMode to item 2 of argv

  set promptText to do shell script "/bin/cat " & quoted form of promptFile
  set the clipboard to promptText

  tell application "Cursor" to activate
  delay 1

  tell application "System Events"
    if not (exists process "Cursor") then error "Cursor process is not available"
    tell process "Cursor"
      set frontmost to true

      if exists window "Cursor Agents" then
        tell window "Cursor Agents" to set focused to true
        if my setFirstTextArea(window "Cursor Agents", promptText, 0) then
          if submitMode is "submit" then
            key code 36 using command down
          end if
          return
        end if
      end if

      if (count of windows) is 0 then error "Cursor has no open window"
      tell front window to set focused to true
      keystroke "i" using command down
      delay 0.5
      keystroke "a" using command down
      delay 0.1
      keystroke "v" using command down
      if submitMode is "submit" then
        delay 0.2
        key code 36 using command down
      end if
    end tell
  end tell
end run

on setFirstTextArea(theElement, promptText, depth)
  tell application "System Events"
    try
      if (role of theElement as text) is "AXTextArea" then
        set focused of theElement to true
        set value of theElement to promptText
        return true
      end if
    end try
    if depth < 30 then
      try
        set nextDepth to depth + 1
        set children to UI elements of theElement
        repeat with childElement in children
          if my setFirstTextArea(childElement, promptText, nextDepth) then return true
        end repeat
      end try
    end if
  end tell
  return false
end setFirstTextArea
