// 桌面端抽屉遮罩层 - 点击关闭抽屉
(() => {
  const init = () => {
    const container = document.querySelector(".md-container")
    if (!container || container.querySelector(".cyb-drawer-backdrop")) return
    const backdrop = document.createElement("label")
    backdrop.className = "cyb-drawer-backdrop"
    backdrop.setAttribute("for", "__drawer")
    container.prepend(backdrop)
  }
  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(init)
  } else {
    document.addEventListener("DOMContentLoaded", init)
  }
})()
