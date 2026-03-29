(() => {
  const setupFloatingDrawerToggle = () => {
    const drawer = document.querySelector("#__drawer")
    if (!drawer) return

    let btn = document.querySelector(".cyb-drawer-toggle")
    if (!btn) {
      btn = document.createElement("button")
      btn.className = "cyb-drawer-toggle"
      btn.type = "button"
      document.body.appendChild(btn)
    }

    const update = () => {
      btn.textContent = drawer.checked ? "×" : "☰"
      btn.setAttribute("aria-label", drawer.checked ? "关闭导航" : "打开导航")
      btn.classList.toggle("is-open", drawer.checked)
    }

    if (btn._drawerListener) {
      drawer.removeEventListener("change", btn._drawerListener)
    }
    btn._drawerListener = update
    drawer.addEventListener("change", btn._drawerListener)

    btn.onclick = () => {
      drawer.checked = !drawer.checked
      drawer.dispatchEvent(new Event("change", { bubbles: true }))
      update()
    }

    update()
  }

  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(setupFloatingDrawerToggle)
  } else {
    document.addEventListener("DOMContentLoaded", setupFloatingDrawerToggle)
  }
})()
