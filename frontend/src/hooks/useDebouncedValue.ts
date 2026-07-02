import { useEffect, useState } from 'react'

/** Returns `value` after it has stopped changing for `delayMs` — used to key
 * search queries so typing doesn't fire one API request per keystroke. */
export function useDebouncedValue<T>(value: T, delayMs = 350): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs)
    return () => clearTimeout(timer)
  }, [value, delayMs])
  return debounced
}
