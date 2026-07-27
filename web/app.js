const CONSTANTS = {
  mainTextHeight: 0.2472,
  mainTextSpacing: 0.021875,
  mainTextHeightTwoLines: 0.184,
  mainTextSpacingTwoLines: 0.00165,
  secondLineTextHeight: 0.108,
  secondLineSpacing: 0.0015,
  secondLinePositionY: 0.924,
  subtitleTextHeight: 0.025,
  subtitleTextHeightTwoLines: 0.029,
  subtitleBlockSpacing: 1,
  subtitleGroupSpacing: 0.0113,
  subtitlePositionSpacing: 0.004,
  dynamicSpacingMin: 0.002,
  dynamicSpacingDecay: 1,
};

const els = {
  canvas: document.querySelector("#outputCanvas"),
  stage: document.querySelector("#canvasStage"),
  width: document.querySelector("#widthInput"),
  height: document.querySelector("#heightInput"),
  mainText: document.querySelector("#mainTextInput"),
  secondText: document.querySelector("#secondTextInput"),
  subtitle: document.querySelector("#subtitleToggle"),
  shadow: document.querySelector("#shadowToggle"),
  opacity: document.querySelector("#opacityInput"),
  opacityValue: document.querySelector("#opacityValue"),
  opacityField: document.querySelector("#opacityField"),
  backgroundInput: document.querySelector("#backgroundInput"),
  backgroundDrop: document.querySelector("#backgroundDrop"),
  backgroundLabel: document.querySelector("#backgroundLabel"),
  backgroundHint: document.querySelector("#backgroundHint"),
  clearBackground: document.querySelector("#clearBackground"),
  presets: document.querySelector(".presets"),
  renderState: document.querySelector("#renderState"),
  sizeLabel: document.querySelector("#sizeLabel"),
  zoomLabel: document.querySelector("#zoomLabel"),
  export: document.querySelector("#exportButton"),
  reset: document.querySelector("#resetButton"),
  toast: document.querySelector("#toast"),
};

const DEFAULTS = {
  width: 1920,
  height: 1080,
  mainText: "协议已确认",
  secondText: "",
  subtitle: false,
  shadow: false,
  opacity: 15,
};

let backgroundBitmap = null;
let wubi98 = {};
let renderTimer = null;
let toastTimer = null;
let renderVersion = 0;
let resourcesReady = false;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function makeCanvas(width, height) {
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.ceil(width));
  canvas.height = Math.max(1, Math.ceil(height));
  return canvas;
}

function isChinese(character) {
  return /[\u3007\u4e00-\ufa29]/u.test(character);
}

function fontForCharacter(character, size) {
  return `900 ${Math.max(1, Math.round(size))}px ${
    isChinese(character) ? '"Endfield Sans"' : '"Novecento"'
  }`;
}

function measureCharacter(ctx, character, size, fontFamily = null) {
  ctx.font = fontFamily
    ? `${Math.max(1, Math.round(size))}px ${fontFamily}`
    : fontForCharacter(character, size);
  const metrics = ctx.measureText(character);
  return {
    width: Math.max(1, metrics.width),
    ascent: metrics.actualBoundingBoxAscent || size * 0.82,
    descent: metrics.actualBoundingBoxDescent || size * 0.18,
    font: ctx.font,
  };
}

function createTextLayer(text, fontSize, spacing = 0) {
  if (!text) return makeCanvas(1, 1);

  const scratch = makeCanvas(1, 1);
  const measureCtx = scratch.getContext("2d");
  const characters = Array.from(text);
  const measurements = characters.map((character) =>
    measureCharacter(measureCtx, character, fontSize),
  );
  const ascent = Math.max(...measurements.map((item) => item.ascent));
  const descent = Math.max(...measurements.map((item) => item.descent));
  const padding = Math.max(2, Math.ceil(fontSize * 0.025));
  const contentWidth =
    measurements.reduce((sum, item) => sum + item.width, 0) +
    spacing * Math.max(0, measurements.length - 1);
  const layer = makeCanvas(contentWidth + padding * 2, ascent + descent + padding * 2);
  const ctx = layer.getContext("2d");
  ctx.fillStyle = "#ffffff";
  ctx.textBaseline = "alphabetic";
  ctx.imageSmoothingEnabled = true;

  let x = padding;
  const baseline = padding + ascent;
  measurements.forEach((item, index) => {
    ctx.font = item.font;
    ctx.fillText(characters[index], x, baseline);
    x += item.width + spacing;
  });
  return layer;
}

function drawGlyphLine(ctx, text, x, baseline, fontSize) {
  ctx.font = `${Math.max(1, Math.round(fontSize))}px "Endfield Glyph"`;
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#ffffff";
  for (const character of Array.from(text)) {
    ctx.fillText(character, x, baseline);
    x += Math.max(1, ctx.measureText(character).width);
  }
}

function measureGlyphLine(ctx, text, fontSize) {
  ctx.font = `${Math.max(1, Math.round(fontSize))}px "Endfield Glyph"`;
  return Array.from(text).reduce(
    (width, character) => width + Math.max(1, ctx.measureText(character).width),
    0,
  );
}

function createSubtitleLayer(text, fontSize) {
  const cleanText = Array.from(text).filter(
    (character) => !/[·’!"#$%&'()＃！（）*+,\-./:;<=>?@，：？￥★、…．＞【】［］《》“”‘’[\]\\^_`{|}~\s]/u.test(character),
  );
  if (!cleanText.length) return makeCanvas(1, 1);

  const codes = cleanText.map((character) => {
    const code = wubi98[character]?.[0] || character;
    return String(code).toUpperCase();
  });
  const scratch = makeCanvas(1, 1);
  const measureCtx = scratch.getContext("2d");
  const lineHeight = Math.max(2, Math.ceil(fontSize * 0.82));
  const blocks = codes.map((code) => {
    const top = code.slice(0, 2);
    const bottom = code.slice(2);
    const topWidth = measureGlyphLine(measureCtx, top, fontSize);
    const bottomWidth = measureGlyphLine(measureCtx, bottom, fontSize);
    const width = Math.max(1, Math.ceil(Math.max(topWidth, bottomWidth)));
    const height = bottom ? lineHeight * 2 : lineHeight;
    const block = makeCanvas(width, height);
    const ctx = block.getContext("2d");
    drawGlyphLine(ctx, top, 0, lineHeight * 0.9, fontSize);
    if (bottom) {
      drawGlyphLine(ctx, bottom, 0, lineHeight * 1.9, fontSize);
    }
    return block;
  });

  const totalWidth =
    blocks.reduce((sum, block) => sum + block.width, 0) +
    CONSTANTS.subtitleBlockSpacing * Math.max(0, blocks.length - 1);
  const maxHeight = Math.max(...blocks.map((block) => block.height));
  const layer = makeCanvas(totalWidth, maxHeight);
  const ctx = layer.getContext("2d");
  let x = 0;
  blocks.forEach((block) => {
    ctx.drawImage(block, x, Math.floor((maxHeight - block.height) / 2));
    x += block.width + CONSTANTS.subtitleBlockSpacing;
  });
  applyBottomAlphaFade(layer, 0.5, 0.05);
  return layer;
}

function applyTopAlphaFade(canvas, fadeRatio = 0.3) {
  const ctx = canvas.getContext("2d");
  ctx.save();
  ctx.globalCompositeOperation = "destination-in";
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "rgba(0,0,0,0)");
  gradient.addColorStop(clamp(fadeRatio, 0.01, 1), "rgba(0,0,0,1)");
  gradient.addColorStop(1, "rgba(0,0,0,1)");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.restore();
}

function applyBottomAlphaFade(canvas, startRatio = 0.5, endAlpha = 0.05) {
  const ctx = canvas.getContext("2d");
  ctx.save();
  ctx.globalCompositeOperation = "destination-in";
  const gradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
  gradient.addColorStop(0, "rgba(0,0,0,1)");
  gradient.addColorStop(clamp(startRatio, 0, 0.99), "rgba(0,0,0,1)");
  gradient.addColorStop(1, `rgba(0,0,0,${endAlpha})`);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.restore();
}

function combineHorizontal(layers, spacing) {
  if (layers.length === 1) return layers[0];
  const width =
    layers.reduce((sum, layer) => sum + layer.width, 0) +
    spacing * Math.max(0, layers.length - 1);
  const height = Math.max(...layers.map((layer) => layer.height));
  const combined = makeCanvas(width, height);
  const ctx = combined.getContext("2d");
  let x = 0;
  layers.forEach((layer) => {
    ctx.drawImage(layer, x, Math.floor((height - layer.height) / 2));
    x += layer.width + spacing;
  });
  return combined;
}

function dynamicSpacing(baseSpacing, characterCount) {
  if (characterCount <= 1) return baseSpacing;
  const ratio =
    CONSTANTS.dynamicSpacingMin +
    (baseSpacing - CONSTANTS.dynamicSpacingMin) *
      Math.exp(-CONSTANTS.dynamicSpacingDecay * (characterCount - 1));
  return Math.max(CONSTANTS.dynamicSpacingMin, ratio);
}

function seededRandom(seed) {
  let value = seed >>> 0;
  return () => {
    value = (value * 1664525 + 1013904223) >>> 0;
    return value / 4294967296;
  };
}

function drawShadow(ctx, bounds, opacity, seed) {
  const width = Math.max(8, bounds.width * 1.2);
  const height = Math.max(8, bounds.height * 1.05);
  const centerX = bounds.x + bounds.width / 2;
  const centerY = bounds.y + bounds.height / 2 + bounds.height * 0.22;
  const shadow = makeCanvas(width, height);
  const shadowCtx = shadow.getContext("2d");
  const radius = Math.max(width, height) / 2;

  shadowCtx.save();
  shadowCtx.translate(width / 2, height / 2);
  shadowCtx.scale(1, height / width);
  const gradient = shadowCtx.createRadialGradient(0, 0, 0, 0, 0, radius);
  gradient.addColorStop(0, `rgba(2,4,4,${opacity})`);
  gradient.addColorStop(0.62, `rgba(7,10,9,${opacity * 0.82})`);
  gradient.addColorStop(1, "rgba(8,10,10,0)");
  shadowCtx.fillStyle = gradient;
  shadowCtx.beginPath();
  shadowCtx.arc(0, 0, radius, 0, Math.PI * 2);
  shadowCtx.fill();
  shadowCtx.restore();

  const random = seededRandom(seed + Math.round(width) * 31 + Math.round(height));
  const speckCount = Math.min(1800, Math.max(220, Math.round((width * height) / 950)));
  shadowCtx.fillStyle = `rgba(175,184,180,${opacity * 0.16})`;
  for (let index = 0; index < speckCount; index += 1) {
    const angle = random() * Math.PI * 2;
    const distance = Math.sqrt(random());
    const x = width / 2 + Math.cos(angle) * distance * width * 0.48;
    const y = height / 2 + Math.sin(angle) * distance * height * 0.44;
    const size = 0.5 + random() * 1.6;
    shadowCtx.fillRect(x, y, size, size);
  }

  ctx.drawImage(shadow, centerX - width / 2, centerY - height / 2);
}

function currentDimensions() {
  if (backgroundBitmap) {
    return { width: backgroundBitmap.width, height: backgroundBitmap.height };
  }
  const width = clamp(Number.parseInt(els.width.value, 10) || DEFAULTS.width, 320, 7680);
  const height = clamp(Number.parseInt(els.height.value, 10) || DEFAULTS.height, 320, 7680);
  return { width, height };
}

function render() {
  if (!resourcesReady) return;
  const version = ++renderVersion;
  els.canvas.classList.add("rendering");
  els.renderState.textContent = "正在生成";

  requestAnimationFrame(() => {
    if (version !== renderVersion) return;
    const { width, height } = currentDimensions();
    const mainText = els.mainText.value.trim() || " ";
    const secondText = els.secondText.value.trim();
    const hasSecondLine = Boolean(secondText);
    const ctx = els.canvas.getContext("2d");
    els.canvas.width = width;
    els.canvas.height = height;
    ctx.clearRect(0, 0, width, height);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";

    if (backgroundBitmap) {
      ctx.drawImage(backgroundBitmap, 0, 0, width, height);
    }

    const mainSpacingBase = hasSecondLine
      ? CONSTANTS.mainTextSpacingTwoLines
      : CONSTANTS.mainTextSpacing;
    const spacing = Math.max(
      1,
      Math.round(width * dynamicSpacing(mainSpacingBase, Array.from(mainText).length)),
    );
    const mainFontSize = Math.round(
      height *
        (hasSecondLine ? CONSTANTS.mainTextHeightTwoLines : CONSTANTS.mainTextHeight),
    );
    const layers = [
      {
        canvas: createTextLayer(mainText, mainFontSize, spacing),
        x: 0,
        y: 0,
        type: "main",
      },
    ];

    if (hasSecondLine) {
      const secondLayer = createTextLayer(
        secondText,
        Math.round(height * CONSTANTS.secondLineTextHeight),
        Math.round(width * CONSTANTS.secondLineSpacing),
      );
      applyTopAlphaFade(secondLayer, 0.3);
      layers.push({ canvas: secondLayer, x: 0, y: 0, type: "second" });
    }

    if (els.subtitle.checked) {
      const subtitleLayers = [
        createSubtitleLayer(
          mainText,
          Math.round(
            height *
              (hasSecondLine
                ? CONSTANTS.subtitleTextHeightTwoLines
                : CONSTANTS.subtitleTextHeight),
          ),
        ),
      ];
      if (hasSecondLine) {
        subtitleLayers.push(
          createSubtitleLayer(
            secondText,
            Math.round(height * CONSTANTS.subtitleTextHeightTwoLines),
          ),
        );
      }
      layers.push({
        canvas: combineHorizontal(
          subtitleLayers,
          Math.round(width * CONSTANTS.subtitleGroupSpacing),
        ),
        x: 0,
        y: 0,
        type: "subtitle",
      });
    }

    const maxLayerWidth = Math.max(...layers.map((layer) => layer.canvas.width));
    layers.forEach((layer) => {
      layer.x = Math.floor((maxLayerWidth - layer.canvas.width) / 2);
    });

    const mainLayer = layers.find((layer) => layer.type === "main");
    let currentY = mainLayer.canvas.height;
    const secondLayer = layers.find((layer) => layer.type === "second");
    if (secondLayer) {
      secondLayer.y = Math.round(mainLayer.canvas.height * CONSTANTS.secondLinePositionY);
      currentY = secondLayer.y + secondLayer.canvas.height;
    }
    const subtitleLayer = layers.find((layer) => layer.type === "subtitle");
    if (subtitleLayer) {
      subtitleLayer.y = currentY + Math.round(height * CONSTANTS.subtitlePositionSpacing);
    }

    const minX = Math.min(...layers.map((layer) => layer.x));
    const minY = Math.min(...layers.map((layer) => layer.y));
    const maxX = Math.max(...layers.map((layer) => layer.x + layer.canvas.width));
    const maxY = Math.max(...layers.map((layer) => layer.y + layer.canvas.height));
    const groupWidth = maxX - minX;
    const groupHeight = maxY - minY;
    const originX = Math.floor((width - groupWidth) / 2 - minX);
    const originY = Math.floor((height - groupHeight) / 2 - minY);

    if (els.shadow.checked) {
      drawShadow(
        ctx,
        {
          x: originX + minX,
          y: originY + minY,
          width: groupWidth,
          height: groupHeight,
        },
        Number(els.opacity.value) / 100,
        Array.from(mainText + secondText).reduce(
          (sum, character) => sum + character.codePointAt(0),
          0,
        ),
      );
    }

    [...layers].reverse().forEach((layer) => {
      ctx.drawImage(layer.canvas, originX + layer.x, originY + layer.y);
    });

    els.sizeLabel.textContent = `${width} × ${height}`;
    els.renderState.textContent = "已就绪";
    els.canvas.classList.remove("rendering");
    updateZoom();
  });
}

function scheduleRender(delay = 100) {
  window.clearTimeout(renderTimer);
  els.renderState.textContent = "等待更新";
  renderTimer = window.setTimeout(render, delay);
}

function updateZoom() {
  if (!els.canvas.width) return;
  const rect = els.canvas.getBoundingClientRect();
  const zoom = Math.round((rect.width / els.canvas.width) * 100);
  els.zoomLabel.textContent = `缩放 ${Math.max(1, zoom)}%`;
}

function updatePresets() {
  const { width, height } = currentDimensions();
  document.querySelectorAll("[data-size]").forEach((button) => {
    button.classList.toggle("active", button.dataset.size === `${width}x${height}`);
  });
}

function updateOpacity() {
  const value = Number(els.opacity.value);
  els.opacityValue.textContent = `${value}%`;
  els.opacity.style.setProperty("--range-progress", `${value}%`);
}

function setBackgroundState(enabled) {
  els.width.disabled = enabled;
  els.height.disabled = enabled;
  els.presets.querySelectorAll("button").forEach((button) => {
    button.disabled = enabled;
  });
  els.backgroundDrop.classList.toggle("has-file", enabled);
}

async function loadBackground(file) {
  if (!file || !file.type.startsWith("image/")) {
    showToast("请选择有效的图片文件");
    return;
  }
  try {
    const bitmap = await createImageBitmap(file);
    if (Math.max(bitmap.width, bitmap.height) > 12000) {
      bitmap.close();
      throw new Error("图片边长不能超过 12000px");
    }
    backgroundBitmap?.close?.();
    backgroundBitmap = bitmap;
    els.width.value = bitmap.width;
    els.height.value = bitmap.height;
    els.backgroundLabel.textContent = file.name;
    els.backgroundHint.textContent = `${bitmap.width} × ${bitmap.height} · 本地读取`;
    setBackgroundState(true);
    updatePresets();
    scheduleRender(10);
  } catch (error) {
    showToast(error.message || "背景图片读取失败");
  } finally {
    els.backgroundInput.value = "";
  }
}

function removeBackground() {
  backgroundBitmap?.close?.();
  backgroundBitmap = null;
  els.backgroundLabel.textContent = "添加背景图片";
  els.backgroundHint.textContent = "PNG / JPG / WEBP / BMP";
  setBackgroundState(false);
  updatePresets();
  scheduleRender(10);
}

function showToast(message) {
  window.clearTimeout(toastTimer);
  els.toast.textContent = message;
  els.toast.classList.add("show");
  toastTimer = window.setTimeout(() => els.toast.classList.remove("show"), 2400);
}

function reset() {
  removeBackground();
  els.width.value = DEFAULTS.width;
  els.height.value = DEFAULTS.height;
  els.mainText.value = DEFAULTS.mainText;
  els.secondText.value = DEFAULTS.secondText;
  els.subtitle.checked = DEFAULTS.subtitle;
  els.shadow.checked = DEFAULTS.shadow;
  els.opacity.value = DEFAULTS.opacity;
  els.opacity.disabled = true;
  els.opacityField.classList.add("disabled");
  updateOpacity();
  updatePresets();
  scheduleRender(10);
  showToast("已恢复默认设置");
}

function exportPng() {
  els.export.disabled = true;
  els.export.querySelector("span:first-child").textContent = "正在导出";
  els.canvas.toBlob((blob) => {
    if (!blob) {
      showToast("导出失败，请稍后重试");
      els.export.disabled = false;
      els.export.querySelector("span:first-child").textContent = "导出 PNG";
      return;
    }
    const filenameBase =
      els.mainText.value.trim().replace(/[\\/:*?"<>|]/g, "_").slice(0, 24) || "endfield-text";
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${filenameBase}.png`;
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    els.export.disabled = false;
    els.export.querySelector("span:first-child").textContent = "导出 PNG";
    showToast("PNG 已生成");
  }, "image/png");
}

function bindEvents() {
  [els.width, els.height, els.mainText, els.secondText].forEach((input) => {
    input.addEventListener("input", () => {
      updatePresets();
      scheduleRender();
    });
  });
  [els.width, els.height].forEach((input) => {
    input.addEventListener("change", () => {
      input.value = clamp(Number.parseInt(input.value, 10) || 320, 320, 7680);
      scheduleRender(10);
    });
  });
  [els.subtitle, els.shadow].forEach((input) => {
    input.addEventListener("change", () => scheduleRender(10));
  });
  els.shadow.addEventListener("change", () => {
    els.opacity.disabled = !els.shadow.checked;
    els.opacityField.classList.toggle("disabled", !els.shadow.checked);
  });
  els.opacity.addEventListener("input", () => {
    updateOpacity();
    scheduleRender(40);
  });
  els.presets.addEventListener("click", (event) => {
    const button = event.target.closest("[data-size]");
    if (!button || button.disabled) return;
    const [width, height] = button.dataset.size.split("x").map(Number);
    els.width.value = width;
    els.height.value = height;
    updatePresets();
    scheduleRender(10);
  });
  els.backgroundDrop.addEventListener("click", (event) => {
    if (event.target.closest("#clearBackground")) {
      removeBackground();
      return;
    }
    els.backgroundInput.click();
  });
  els.backgroundInput.addEventListener("change", () =>
    loadBackground(els.backgroundInput.files?.[0]),
  );
  ["dragenter", "dragover"].forEach((eventName) => {
    els.backgroundDrop.addEventListener(eventName, (event) => {
      event.preventDefault();
      els.backgroundDrop.classList.add("dragging");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    els.backgroundDrop.addEventListener(eventName, (event) => {
      event.preventDefault();
      els.backgroundDrop.classList.remove("dragging");
    });
  });
  els.backgroundDrop.addEventListener("drop", (event) =>
    loadBackground(event.dataTransfer?.files?.[0]),
  );
  els.export.addEventListener("click", exportPng);
  els.reset.addEventListener("click", reset);
  new ResizeObserver(updateZoom).observe(els.stage);
}

async function loadResources() {
  bindEvents();
  updateOpacity();
  try {
    const [, , , dictionaryResponse] = await Promise.all([
      document.fonts.load('900 64px "Endfield Sans"'),
      document.fonts.load('900 64px "Novecento"'),
      document.fonts.load('32px "Endfield Glyph"'),
      fetch("./assets/wubi_98.json"),
    ]);
    if (!dictionaryResponse.ok) throw new Error("五笔 98 码表加载失败");
    wubi98 = await dictionaryResponse.json();
    resourcesReady = true;
    render();
  } catch (error) {
    els.renderState.textContent = "资源加载失败";
    showToast(error.message || "资源加载失败");
    console.error(error);
  }
}

loadResources();
