// Liten, avhengighetsfri lightbox.
(() => {
  const box = document.getElementById("lightbox");
  if (!box) return;

  const imgEl = box.querySelector("img");
  const photos = Array.from(document.querySelectorAll(".masonry .photo img"));
  if (!photos.length) return;

  let index = 0;

  function show(i) {
    index = (i + photos.length) % photos.length;
    const src = photos[index].dataset.full || photos[index].src;
    imgEl.src = src;
    imgEl.alt = photos[index].alt || "";
    box.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function hide() {
    box.hidden = true;
    imgEl.src = "";
    document.body.style.overflow = "";
  }

  photos.forEach((img, i) => {
    img.addEventListener("click", () => show(i));
  });

  box.addEventListener("click", (e) => {
    if (e.target === box || e.target === imgEl) hide();
  });
  box.querySelector(".lightbox-close").addEventListener("click", hide);
  box.querySelector(".lightbox-prev").addEventListener("click", (e) => {
    e.stopPropagation();
    show(index - 1);
  });
  box.querySelector(".lightbox-next").addEventListener("click", (e) => {
    e.stopPropagation();
    show(index + 1);
  });

  document.addEventListener("keydown", (e) => {
    if (box.hidden) return;
    if (e.key === "Escape") hide();
    if (e.key === "ArrowLeft") show(index - 1);
    if (e.key === "ArrowRight") show(index + 1);
  });

  // Swipe på touch
  let startX = 0;
  imgEl.addEventListener("touchstart", (e) => { startX = e.touches[0].clientX; }, { passive: true });
  imgEl.addEventListener("touchend", (e) => {
    const dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 60) show(dx < 0 ? index + 1 : index - 1);
  });
})();
