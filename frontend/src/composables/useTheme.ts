import { onMounted, ref } from 'vue'

type Theme = 'light' | 'dark'

const STORAGE_KEY = 'joff-theme'

// The boot script inlined in index.html already sets documentElement's
// data-theme attribute before Vue mounts, to avoid a flash of the wrong theme.
const theme = ref<Theme>('light')

export function useTheme() {
  onMounted(() => {
    theme.value = (document.documentElement.dataset.theme as Theme | undefined) ?? 'light'
  })

  function toggle() {
    theme.value = theme.value === 'dark' ? 'light' : 'dark'
    localStorage.setItem(STORAGE_KEY, theme.value)
    document.documentElement.dataset.theme = theme.value
  }

  return { theme, toggle }
}
