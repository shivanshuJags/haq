// Phones: when the keyboard opens, only the *visible* part of the screen shrinks — the page keeps its
// full height, so the browser slides the whole app up to show the input and the header disappears.
// Fix: keep the app exactly as tall as the visible area (--app-height), keep the page itself from
// scrolling, and mark <html class="keyboard-open"> so less important lines can hide while typing.
// (Android Chrome also gets `interactive-widget=resizes-content` in index.html; iPhone Safari needs this.)

export function fitToVisibleScreen(): void {
  const viewport = window.visualViewport
  if (!viewport) return
  const root = document.documentElement
  let tallest = viewport.height
  let width = viewport.width

  const update = () => {
    if (viewport.width !== width) {
      // Rotated: start measuring again
      width = viewport.width
      tallest = viewport.height
    }
    tallest = Math.max(tallest, viewport.height)
    root.style.setProperty('--app-height', `${viewport.height}px`)
    // A keyboard takes at least a quarter of the screen; smaller changes are browser toolbars
    root.classList.toggle('keyboard-open', viewport.height < tallest * 0.75)
    if (window.scrollY !== 0) window.scrollTo(0, 0) // iPhone slides the page up; put it back
  }

  viewport.addEventListener('resize', update)
  viewport.addEventListener('scroll', update)
  update()
}
