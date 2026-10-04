// ScamShield — Full Application Client Engine (v2.0)
document.addEventListener("DOMContentLoaded", () => {
  // ── Global State ───────────────────────────────────────────────────────────
  let currentFile = null;
  let currentBase64 = null;
  let currentAnalysis = null;
  let currentLanguage = "en";
  let chatHistory = [];
  let qrFile = null;
  let qrBase64 = null;

  // Quiz State
  let quizQuestions = [];
  let quizIndex = 0;
  let quizScore = 0;
  let quizDifficulty = "beginner";

  // Recovery Wizard State
  let wizardData = {
    time: "lt1",
    minutes: 30,
    bank: "",
    bankInfo: null,
    checkedActions: [],
  };
  let bankCatalog = {};

  // ── History LocalStorage Helper ────────────────────────────────────────────
  const STORAGE_KEY = "scamshield_history";

  function getHistory() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];
    } catch {
      return [];
    }
  }

  function saveScanToHistory(scanType, inputPreview, verdict, riskScore, summary) {
    const list = getHistory();
    const entry = {
      id: Date.now(),
      date: new Date().toLocaleString(),
      type: scanType, // 'screenshot' | 'text' | 'url' | 'phone' | 'qr'
      preview: String(inputPreview || "").slice(0, 60),
      verdict: verdict || "SUSPICIOUS",
      score: Number(riskScore) || 50,
      summary: summary || "No summary available.",
    };
    list.unshift(entry);
    if (list.length > 100) list.pop();
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
    renderHistoryTable();
  }

  // ── Languages Setup ────────────────────────────────────────────────────────
  const langSelect = document.getElementById("lang-select");

  async function initLanguages() {
    try {
      const res = await fetch("/api/languages");
      const json = await res.json();
      if (json.success && json.languages) {
        langSelect.innerHTML = "";
        for (const [code, name] of Object.entries(json.languages)) {
          const opt = document.createElement("option");
          opt.value = code;
          opt.textContent = name;
          if (code === "en") opt.selected = true;
          langSelect.appendChild(opt);
        }
      }
    } catch (e) {
      console.warn("Using fallback language options:", e);
    }
  }

  langSelect.addEventListener("change", (e) => {
    currentLanguage = e.target.value;
  });

  // ── Tab Switching ──────────────────────────────────────────────────────────
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  function switchTab(targetTab) {
    tabBtns.forEach((btn) => {
      const isActive = btn.getAttribute("data-tab") === targetTab;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive);
    });

    tabContents.forEach((content) => {
      content.classList.toggle("active", content.id === `tab-${targetTab}`);
    });

    if (targetTab === "history") renderHistoryTable();
    if (targetTab === "community") loadRecentCommunityReports();
    if (targetTab === "recovery" && Object.keys(bankCatalog).length === 0) loadBankCatalog();
  }

  tabBtns.forEach((btn) => {
    btn.addEventListener("click", () => switchTab(btn.getAttribute("data-tab")));
  });

  // ── SCANNER: Sub-Mode Toggle (Screenshot vs Text) ─────────────────────────
  const scanModeBtns = document.querySelectorAll(".scan-mode-btn");
  const scanModePanels = document.querySelectorAll(".scan-mode-panel");

  scanModeBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const mode = btn.getAttribute("data-mode");
      scanModeBtns.forEach((b) => b.classList.toggle("active", b === btn));
      document.getElementById("scan-mode-screenshot").classList.toggle("active", mode === "screenshot");
      document.getElementById("scan-mode-text").classList.toggle("active", mode === "text");
    });
  });

  // ── SCANNER 1: Screenshot Vision Upload & Analysis ─────────────────────────
  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const previewWrap = document.getElementById("preview-wrap");
  const previewImg = document.getElementById("preview-img");
  const removeImgBtn = document.getElementById("remove-img-btn");
  const senderInput = document.getElementById("sender-input");
  const analyzeBtn = document.getElementById("analyze-btn");
  const analyzeSpinner = document.getElementById("analyze-spinner");

  const emptyState = document.getElementById("empty-state");
  const verdictContainer = document.getElementById("verdict-container");
  const verdictBadge = document.getElementById("verdict-badge");
  const chartScore = document.getElementById("chart-score");
  const circularChart = document.getElementById("circular-chart");
  const legitBanner = document.getElementById("legit-banner");
  const summaryText = document.getElementById("summary-text");
  const redFlagsList = document.getElementById("red-flags-list");
  const redFlagsBox = document.getElementById("red-flags-box");
  const actionList = document.getElementById("action-list");
  const reasoningText = document.getElementById("reasoning-text");

  const sendToChatBtn = document.getElementById("send-to-chat-btn");
  const sendToAlertBtn = document.getElementById("send-to-alert-btn");

  dropZone.addEventListener("click", (e) => {
    if (e.target !== removeImgBtn) fileInput.click();
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("dragover"));

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) handleFile(e.target.files[0]);
  });

  removeImgBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    clearImage();
  });

  function clearImage() {
    currentFile = null;
    currentBase64 = null;
    previewImg.src = "";
    previewWrap.style.display = "none";
    dropZone.querySelector(".drop-zone-content").style.display = "block";
    fileInput.value = "";
    analyzeBtn.disabled = true;
    document.querySelectorAll(".sample-chip").forEach((c) => c.classList.remove("active"));
  }

  function handleFile(file, autoAnalyze = false) {
    currentFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      currentBase64 = e.target.result;
      previewImg.src = currentBase64;
      previewWrap.style.display = "block";
      dropZone.querySelector(".drop-zone-content").style.display = "none";
      analyzeBtn.disabled = false;
      if (autoAnalyze) runAnalysis();
    };
    reader.readAsDataURL(file);
  }

  // Quick Test Sample Chips
  document.querySelectorAll(".sample-chip").forEach((chip) => {
    chip.addEventListener("click", async () => {
      const fileName = chip.getAttribute("data-file");
      document.querySelectorAll(".sample-chip").forEach((c) => c.classList.remove("active"));
      chip.classList.add("active");

      if (fileName.includes("login_otp")) senderInput.value = "VK-AMZNOT";
      else if (fileName.includes("bank_alert")) senderInput.value = "AD-HDFCBK";
      else if (fileName.includes("swiggy")) senderInput.value = "SWIGGY";
      else if (fileName.includes("irctc")) senderInput.value = "IRCTC";
      else senderInput.value = "";

      try {
        let res = await fetch(`/samples/${fileName}`);
        if (!res.ok) res = await fetch(`/api/sample/${fileName}`);
        if (!res.ok) throw new Error("Failed to load sample image");
        const blob = await res.blob();
        handleFile(new File([blob], fileName, { type: "image/png" }), true);
      } catch (err) {
        console.error("Sample load error:", err);
      }
    });
  });

  async function runAnalysis() {
    if (!currentFile && !currentBase64) return;
    analyzeBtn.disabled = true;
    analyzeSpinner.style.display = "inline-block";
    emptyState.style.display = "none";
    verdictContainer.style.display = "none";

    try {
      const payload = {
        image_base64: currentBase64,
        language: currentLanguage,
        sender_id: senderInput.value.trim() || null,
      };

      const res = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "Analysis failed");

      renderVerdict(json.data, "screenshot", currentFile ? currentFile.name : "Uploaded Screenshot");
    } catch (err) {
      alert(`Analysis error: ${err.message}`);
      emptyState.style.display = "flex";
    } finally {
      analyzeBtn.disabled = false;
      analyzeSpinner.style.display = "none";
    }
  }

  analyzeBtn.addEventListener("click", runAnalysis);

  function renderVerdict(data, scanType = "screenshot", preview = "Screenshot") {
    currentAnalysis = data;
    emptyState.style.display = "none";
    verdictContainer.style.display = "block";

    const verdict = data.verdict || "SAFE";
    const score = Number(data.risk_score) || 0;

    verdictBadge.textContent = verdict;
    verdictBadge.className = `verdict-badge ${verdict}`;
    chartScore.textContent = score;

    if (verdict === "SAFE") {
      circularChart.style.borderColor = "var(--safe-green)";
      circularChart.style.boxShadow = "0 0 16px var(--safe-glow)";
      legitBanner.style.display = "flex";
    } else if (verdict === "SUSPICIOUS") {
      circularChart.style.borderColor = "var(--warning-amber)";
      circularChart.style.boxShadow = "0 0 16px var(--warning-glow)";
      legitBanner.style.display = "none";
    } else {
      circularChart.style.borderColor = "var(--scam-red)";
      circularChart.style.boxShadow = "0 0 20px var(--scam-glow)";
      legitBanner.style.display = "none";
    }

    summaryText.textContent = data.summary || "No summary provided.";

    redFlagsList.innerHTML = "";
    if (data.red_flags && data.red_flags.length > 0) {
      redFlagsBox.style.display = "block";
      data.red_flags.forEach((f) => {
        const li = document.createElement("li");
        li.textContent = `⚠️ ${f}`;
        redFlagsList.appendChild(li);
      });
    } else {
      redFlagsBox.style.display = "none";
    }

    actionList.innerHTML = "";
    const items = data.action_items || [data.advice] || [];
    items.forEach((a) => {
      const li = document.createElement("li");
      li.textContent = `🛡️ ${a}`;
      actionList.appendChild(li);
    });

    reasoningText.textContent = data.reasoning || data.details || "Direct model response verified.";

    updateAlertPreview(data);
    document.getElementById("scan-context-badge").style.display = "inline-flex";

    // Auto-save scan to history
    saveScanToHistory(scanType, preview, verdict, score, data.summary);
  }

  sendToChatBtn.addEventListener("click", () => {
    switchTab("chat");
    if (currentAnalysis) {
      document.getElementById("chat-input").value = `Can you explain why this was marked as ${currentAnalysis.verdict}?`;
      document.getElementById("chat-input").focus();
    }
  });

  sendToAlertBtn.addEventListener("click", () => switchTab("alerts"));

  // ── SCANNER 2: Text / SMS Message Analyzer ─────────────────────────────────
  const textScanInput = document.getElementById("text-scan-input");
  const textAnalyzeBtn = document.getElementById("text-analyze-btn");
  const textAnalyzeSpinner = document.getElementById("text-analyze-spinner");
  const textEmptyState = document.getElementById("text-empty-state");
  const textVerdictContainer = document.getElementById("text-verdict-container");
  const textVerdictBadge = document.getElementById("text-verdict-badge");
  const textChartScore = document.getElementById("text-chart-score");
  const textCircularChart = document.getElementById("text-circular-chart");
  const textLegitBanner = document.getElementById("text-legit-banner");
  const textSummaryText = document.getElementById("text-summary-text");
  const textRedFlagsList = document.getElementById("text-red-flags-list");
  const textRedFlagsBox = document.getElementById("text-red-flags-box");
  const textActionList = document.getElementById("text-action-list");
  const textReasoningText = document.getElementById("text-reasoning-text");

  textAnalyzeBtn.addEventListener("click", async () => {
    const text = textScanInput.value.trim();
    if (!text) {
      alert("Please paste a message text first.");
      return;
    }

    textAnalyzeBtn.disabled = true;
    textAnalyzeSpinner.style.display = "inline-block";
    textEmptyState.style.display = "none";
    textVerdictContainer.style.display = "none";

    try {
      const res = await fetch("/api/scan/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, language: currentLanguage }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "Text scan failed");

      const data = json.data;
      currentAnalysis = data;
      textVerdictContainer.style.display = "block";

      const verdict = data.verdict || "SAFE";
      const score = Number(data.risk_score) || 0;

      textVerdictBadge.textContent = verdict;
      textVerdictBadge.className = `verdict-badge ${verdict}`;
      textChartScore.textContent = score;

      if (verdict === "SAFE") {
        textCircularChart.style.borderColor = "var(--safe-green)";
        textCircularChart.style.boxShadow = "0 0 16px var(--safe-glow)";
        textLegitBanner.style.display = "flex";
      } else if (verdict === "SUSPICIOUS") {
        textCircularChart.style.borderColor = "var(--warning-amber)";
        textCircularChart.style.boxShadow = "0 0 16px var(--warning-glow)";
        textLegitBanner.style.display = "none";
      } else {
        textCircularChart.style.borderColor = "var(--scam-red)";
        textCircularChart.style.boxShadow = "0 0 20px var(--scam-glow)";
        textLegitBanner.style.display = "none";
      }

      textSummaryText.textContent = data.summary || "No summary provided.";

      textRedFlagsList.innerHTML = "";
      if (data.red_flags && data.red_flags.length > 0) {
        textRedFlagsBox.style.display = "block";
        data.red_flags.forEach((f) => {
          const li = document.createElement("li");
          li.textContent = `⚠️ ${f}`;
          textRedFlagsList.appendChild(li);
        });
      } else {
        textRedFlagsBox.style.display = "none";
      }

      textActionList.innerHTML = "";
      const acts = data.action_items || [data.advice] || [];
      acts.forEach((a) => {
        const li = document.createElement("li");
        li.textContent = `🛡️ ${a}`;
        textActionList.appendChild(li);
      });

      textReasoningText.textContent = data.reasoning || "Direct text pattern & model analysis verified.";

      updateAlertPreview(data);
      saveScanToHistory("text", text, verdict, score, data.summary);
    } catch (err) {
      alert(`Text scan error: ${err.message}`);
      textEmptyState.style.display = "flex";
    } finally {
      textAnalyzeBtn.disabled = false;
      textAnalyzeSpinner.style.display = "none";
    }
  });

  document.getElementById("text-send-to-chat-btn")?.addEventListener("click", () => switchTab("chat"));
  document.getElementById("text-send-to-alert-btn")?.addEventListener("click", () => switchTab("alerts"));

  // ── SCANNER 3: URL Phishing Detector ───────────────────────────────────────
  const urlInput = document.getElementById("url-input");
  const urlClearBtn = document.getElementById("url-clear-btn");
  const urlScanBtn = document.getElementById("url-scan-btn");
  const urlSpinner = document.getElementById("url-spinner");
  const urlResults = document.getElementById("url-results");

  urlClearBtn.addEventListener("click", () => {
    urlInput.value = "";
    urlResults.style.display = "none";
  });

  urlScanBtn.addEventListener("click", async () => {
    const rawUrl = urlInput.value.trim();
    if (!rawUrl) {
      alert("Please enter a URL to scan.");
      return;
    }

    urlScanBtn.disabled = true;
    urlSpinner.style.display = "inline-block";
    urlResults.style.display = "none";

    try {
      const res = await fetch("/api/scan/url", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: rawUrl }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "URL scan failed");

      const d = json.data;
      urlResults.style.display = "block";

      const verdict = d.verdict || "SAFE";
      const score = Number(d.risk_score) || 0;

      const badge = document.getElementById("url-verdict-badge");
      badge.textContent = verdict;
      badge.className = `verdict-badge ${verdict}`;

      document.getElementById("url-chart-score").textContent = score;
      const chart = document.getElementById("url-circular-chart");
      chart.style.borderColor = verdict === "SAFE" ? "var(--safe-green)" : (verdict === "SUSPICIOUS" ? "var(--warning-amber)" : "var(--scam-red)");

      document.getElementById("url-domain").textContent = d.domain || "—";
      document.getElementById("url-whois").textContent = d.whois_info?.registrar || d.whois_info?.creation_date || "Not disclosed";
      document.getElementById("url-expanded").textContent = d.is_shortened ? d.redirect_url : (d.domain || "Direct URL");
      document.getElementById("url-age").textContent = d.whois_info?.age_days ? `${d.whois_info.age_days} days` : "Unknown";

      // Threats box
      const threatsBox = document.getElementById("url-threats-box");
      const threatsList = document.getElementById("url-threats-list");
      threatsList.innerHTML = "";
      if (d.threats && d.threats.length > 0) {
        threatsBox.style.display = "block";
        d.threats.forEach((t) => {
          const li = document.createElement("li");
          li.textContent = `🚨 ${t}`;
          threatsList.appendChild(li);
        });
      } else {
        threatsBox.style.display = "none";
      }

      saveScanToHistory("url", rawUrl, verdict, score, `Domain: ${d.domain}`);
    } catch (err) {
      alert(`URL scan error: ${err.message}`);
    } finally {
      urlScanBtn.disabled = false;
      urlSpinner.style.display = "none";
    }
  });

  // ── SCANNER 4: Phone & QR Code Sub-Tabs ─────────────────────────────────────
  const subTabBtns = document.querySelectorAll(".sub-tab-btn");
  subTabBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-subtab");
      subTabBtns.forEach((b) => b.classList.toggle("active", b === btn));
      document.getElementById("subtab-phone").classList.toggle("active", target === "phone");
      document.getElementById("subtab-qr").classList.toggle("active", target === "qr");
    });
  });

  // Phone Lookup
  const phoneInput = document.getElementById("phone-input");
  const phoneLookupBtn = document.getElementById("phone-lookup-btn");
  const phoneSpinner = document.getElementById("phone-spinner");
  const phoneResults = document.getElementById("phone-results");

  phoneLookupBtn.addEventListener("click", async () => {
    const rawPhone = phoneInput.value.trim();
    if (!rawPhone || rawPhone.length < 10) {
      alert("Please enter a valid 10-digit mobile number.");
      return;
    }

    phoneLookupBtn.disabled = true;
    phoneSpinner.style.display = "inline-block";
    phoneResults.style.display = "none";

    try {
      const res = await fetch("/api/scan/phone", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: `+91${rawPhone}` }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "Phone lookup failed");

      const d = json.data;
      phoneResults.style.display = "block";

      const verdict = d.verdict || "SAFE";
      const score = Number(d.risk_score) || 0;

      const badge = document.getElementById("phone-verdict-badge");
      badge.textContent = verdict;
      badge.className = `verdict-badge ${verdict}`;

      document.getElementById("phone-chart-score").textContent = score;
      document.getElementById("phone-carrier").textContent = d.carrier || "Indian Telecom Carrier";
      document.getElementById("phone-truecaller").textContent = d.truecaller_name || "Unverified Identity";
      document.getElementById("phone-type").textContent = d.is_voip ? "VoIP / Virtual Phone" : "Mobile GSM";
      document.getElementById("phone-spam-count").textContent = `${d.spam_reports || 0} reports`;

      const spamPct = `${score}%`;
      document.getElementById("phone-spam-pct").textContent = spamPct;
      const fill = document.getElementById("phone-spam-fill");
      fill.style.width = spamPct;
      fill.style.background = score > 60 ? "var(--scam-red)" : (score > 30 ? "var(--warning-amber)" : "var(--safe-green)");

      saveScanToHistory("phone", `+91 ${rawPhone}`, verdict, score, `Carrier: ${d.carrier || "GSM"}`);
    } catch (err) {
      alert(`Phone scan error: ${err.message}`);
    } finally {
      phoneLookupBtn.disabled = false;
      phoneSpinner.style.display = "none";
    }
  });

  // QR Scanner
  const qrDropZone = document.getElementById("qr-drop-zone");
  const qrFileInput = document.getElementById("qr-file-input");
  const qrPreviewWrap = document.getElementById("qr-preview-wrap");
  const qrPreviewImg = document.getElementById("qr-preview-img");
  const qrRemoveBtn = document.getElementById("qr-remove-btn");
  const qrScanBtn = document.getElementById("qr-scan-btn");
  const qrSpinner = document.getElementById("qr-spinner");
  const qrResults = document.getElementById("qr-results");

  qrDropZone.addEventListener("click", (e) => {
    if (e.target !== qrRemoveBtn) qrFileInput.click();
  });

  qrFileInput.addEventListener("change", (e) => {
    if (e.target.files.length) handleQrFile(e.target.files[0]);
  });

  qrRemoveBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    qrFile = null;
    qrBase64 = null;
    qrPreviewImg.src = "";
    qrPreviewWrap.style.display = "none";
    document.getElementById("qr-dz-content").style.display = "block";
    qrScanBtn.disabled = true;
    qrResults.style.display = "none";
  });

  function handleQrFile(file) {
    qrFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      qrBase64 = e.target.result;
      qrPreviewImg.src = qrBase64;
      qrPreviewWrap.style.display = "block";
      document.getElementById("qr-dz-content").style.display = "none";
      qrScanBtn.disabled = false;
    };
    reader.readAsDataURL(file);
  }

  qrScanBtn.addEventListener("click", async () => {
    if (!qrBase64) return;
    qrScanBtn.disabled = true;
    qrSpinner.style.display = "inline-block";
    qrResults.style.display = "none";

    try {
      const res = await fetch("/api/scan/qr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_base64: qrBase64 }),
      });
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "QR scan failed");

      const d = json.data;
      qrResults.style.display = "block";

      const verdict = d.verdict || "SAFE";
      const score = Number(d.risk_score) || 0;

      const badge = document.getElementById("qr-verdict-badge");
      badge.textContent = verdict;
      badge.className = `verdict-badge ${verdict}`;

      document.getElementById("qr-chart-score").textContent = score;
      document.getElementById("qr-decoded-value").textContent = d.decoded_value || "—";
      document.getElementById("qr-assessment").textContent = d.summary || (verdict === "SAFE" ? "Genuine QR code detected." : "Caution: Suspicious payload encoded.");

      saveScanToHistory("qr", d.decoded_value, verdict, score, d.summary);
    } catch (err) {
      alert(`QR scan error: ${err.message}`);
    } finally {
      qrScanBtn.disabled = false;
      qrSpinner.style.display = "none";
    }
  });

  // ── AI ASSISTANT: Chat Thread ──────────────────────────────────────────────
  const chatThread = document.getElementById("chat-thread");
  const chatInput = document.getElementById("chat-input");
  const chatSendBtn = document.getElementById("chat-send-btn");
  const chatSpinner = document.getElementById("chat-spinner");

  // ── RICH MARKDOWN & KATEX LATEX RENDERING ENGINE ──────────────────────────
  function renderRichContent(rawText, container) {
    if (!rawText) {
      container.innerHTML = "";
      return;
    }

    let parsedHtml = "";

    // Pre-process high-priority scam alert banners
    let processedText = rawText
      .replace(/^>\s*🛑\s*\*\*([^*]+)\*\*/gm, '<div class="chat-alert-box">🛑 <strong>$1</strong></div>')
      .replace(/\*\*STOP IMMEDIATELY[^*]*\*\*/g, '<span class="chat-alert-box" style="display:inline-block;padding:4px 10px;margin:2px 0;">🛑 <strong>$&</strong></span>');

    if (window.marked && typeof window.marked.parse === "function") {
      try {
        const rawHtml = window.marked.parse(processedText);
        parsedHtml = window.DOMPurify && typeof window.DOMPurify.sanitize === "function"
          ? window.DOMPurify.sanitize(rawHtml)
          : rawHtml;
      } catch (e) {
        console.warn("Marked parse error:", e);
        parsedHtml = fallbackMarkdown(processedText);
      }
    } else {
      parsedHtml = fallbackMarkdown(processedText);
    }

    container.innerHTML = `<div class="md-content">${parsedHtml}</div>`;

    // Render KaTeX Math Expressions ($...$, $$...$$, \(...\), \[...\])
    try {
      if (window.renderMathInElement && typeof window.renderMathInElement === "function") {
        window.renderMathInElement(container, {
          delimiters: [
            { left: "$$", right: "$$", display: true },
            { left: "$", right: "$", display: false },
            { left: "\\(", right: "\\)", display: false },
            { left: "\\[", right: "\\]", display: true },
          ],
          throwOnError: false,
        });
      } else if (window.katex && typeof window.katex.renderToString === "function") {
        const el = container.querySelector(".md-content");
        if (el) {
          el.innerHTML = el.innerHTML.replace(/\$([^$]+)\$/g, (match, expr) => {
            try {
              return window.katex.renderToString(expr, { throwOnError: false, displayMode: false });
            } catch (err) {
              return `<span class="math-fallback">${expr}</span>`;
            }
          });
        }
      } else {
        const el = container.querySelector(".md-content");
        if (el) {
          el.innerHTML = el.innerHTML.replace(/\$([^$]+)\$/g, '<span class="math-fallback font-mono font-italic">$1</span>');
        }
      }
    } catch (kErr) {
      console.warn("KaTeX render error:", kErr);
    }
  }

  function fallbackMarkdown(txt) {
    if (!txt) return "";
    return txt
      .replace(/### (.*?)\n/g, "<h3>$1</h3>")
      .replace(/## (.*?)\n/g, "<h2>$1</h2>")
      .replace(/# (.*?)\n/g, "<h1>$1</h1>")
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" rel="noopener">$1 ↗</a>')
      .replace(/^\* (.*?)$/gm, "<li>$1</li>")
      .replace(/^\d+\. (.*?)$/gm, "<li>$1</li>")
      .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
      .replace(/\n\n/g, "<p></p>")
      .replace(/\n/g, "<br>");
  }

  async function sendChatMessage(userText) {
    if (!userText.trim()) return;
    appendBubble("user", userText);
    chatInput.value = "";
    chatHistory.push({ role: "user", content: userText });

    const botBubble = appendBubble("bot", "Analyzing safety vectors & threat database...", true);
    chatSendBtn.disabled = true;
    chatSpinner.style.display = "inline-block";

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: chatHistory,
          language: currentLanguage,
          scan_context: currentAnalysis,
        }),
      });

      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "Chat failed");

      renderRichContent(json.reply, botBubble.querySelector(".bubble-body"));
      chatHistory.push({ role: "assistant", content: json.reply });
    } catch (err) {
      botBubble.querySelector(".bubble-body").innerHTML = `<div class="chat-alert-box" style="margin:0;">🚨 Error: ${err.message}</div>`;
    } finally {
      chatSendBtn.disabled = false;
      chatSpinner.style.display = "none";
    }
  }

  function appendBubble(role, text, isPending = false) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role === "user" ? "user-bubble" : "bot-bubble"}`;
    bubble.innerHTML = `
      <div class="bubble-avatar">${role === "user" ? "👤" : "🛡️"}</div>
      <div class="bubble-body">
        <div class="md-content"></div>
      </div>
    `;
    const bodyContent = bubble.querySelector(".md-content");
    if (isPending) {
      bodyContent.innerHTML = `<span style="display:inline-flex;align-items:center;gap:8px;"><span class="btn-spinner light"></span> ${text}</span>`;
    } else {
      renderRichContent(text, bodyContent);
    }
    chatThread.appendChild(bubble);
    chatThread.scrollTop = chatThread.scrollHeight;
    return bubble;
  }

  chatSendBtn.addEventListener("click", () => sendChatMessage(chatInput.value));
  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendChatMessage(chatInput.value);
  });

  document.querySelectorAll(".starter-chip").forEach((chip) => {
    chip.addEventListener("click", () => sendChatMessage(chip.getAttribute("data-prompt")));
  });

  // ── SCAM AWARENESS QUIZ ENGINE ─────────────────────────────────────────────
  const diffBtns = document.querySelectorAll(".diff-btn");
  const quizSetup = document.getElementById("quiz-setup");
  const quizActive = document.getElementById("quiz-active");
  const quizEnd = document.getElementById("quiz-end");
  const quizStartBtn = document.getElementById("quiz-start-btn");
  const quizStartSpinner = document.getElementById("quiz-start-spinner");

  diffBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      diffBtns.forEach((b) => b.classList.remove("selected"));
      btn.classList.add("selected");
      quizDifficulty = btn.getAttribute("data-difficulty");
    });
  });

  quizStartBtn.addEventListener("click", async () => {
    quizStartBtn.disabled = true;
    quizStartSpinner.style.display = "inline-block";

    try {
      const res = await fetch(`/api/quiz?difficulty=${quizDifficulty}&limit=15`);
      const json = await res.json();
      if (!json.success || !json.questions.length) throw new Error("No quiz questions loaded");

      quizQuestions = json.questions;
      quizIndex = 0;
      quizScore = 0;

      quizSetup.style.display = "none";
      quizEnd.style.display = "none";
      quizActive.style.display = "block";

      renderQuizQuestion();
    } catch (err) {
      alert(`Quiz load error: ${err.message}`);
    } finally {
      quizStartBtn.disabled = false;
      quizStartSpinner.style.display = "none";
    }
  });

  function renderQuizQuestion() {
    if (quizIndex >= quizQuestions.length) {
      showQuizEnd();
      return;
    }

    const q = quizQuestions[quizIndex];
    const pct = Math.round((quizIndex / quizQuestions.length) * 100);
    document.getElementById("quiz-progress-bar").style.width = `${pct}%`;
    document.getElementById("quiz-question-counter").textContent = `Question ${quizIndex + 1} / ${quizQuestions.length}`;
    document.getElementById("quiz-score-display").textContent = `🛡️ ${quizScore} Points`;

    const qText = currentLanguage === "hi" && q.question_hi ? q.question_hi : q.question_en;
    document.getElementById("quiz-question-text").textContent = qText;

    const optionsContainer = document.getElementById("quiz-options");
    optionsContainer.innerHTML = "";
    const explanationBox = document.getElementById("quiz-explanation");
    explanationBox.style.display = "none";

    q.options.forEach((opt, idx) => {
      const btn = document.createElement("button");
      btn.className = "quiz-option";
      const txt = currentLanguage === "hi" && opt.text_hi ? opt.text_hi : opt.text;
      const letter = String.fromCharCode(65 + idx);
      btn.innerHTML = `<span class="opt-badge">${letter}</span><span class="opt-text">${txt}</span>`;

      btn.addEventListener("click", () => {
        // Lock options
        optionsContainer.querySelectorAll("button").forEach((b) => (b.disabled = true));

        if (opt.is_correct) {
          btn.classList.add("correct");
          const bEl = btn.querySelector(".opt-badge");
          if (bEl) bEl.textContent = "✓";
          quizScore += q.points || 10;
          document.getElementById("quiz-score-display").textContent = `🛡️ ${quizScore} Points`;
        } else {
          btn.classList.add("wrong");
          const bEl = btn.querySelector(".opt-badge");
          if (bEl) bEl.textContent = "✗";
          // Highlight correct answer
          q.options.forEach((o, i) => {
            if (o.is_correct) {
              const corBtn = optionsContainer.children[i];
              if (corBtn) {
                corBtn.classList.add("correct");
                const corBadge = corBtn.querySelector(".opt-badge");
                if (corBadge) corBadge.textContent = "✓";
              }
            }
          });
        }

        const expl = currentLanguage === "hi" && q.explanation_hi ? q.explanation_hi : q.explanation_en;
        explanationBox.innerHTML = `<strong>💡 Safety Defense Rule:</strong><p style="margin:6px 0 0 0;">${expl}</p>`;
        explanationBox.style.display = "block";

        setTimeout(() => {
          quizIndex++;
          renderQuizQuestion();
        }, 2500);
      });

      optionsContainer.appendChild(btn);
    });
  }

  function showQuizEnd() {
    quizActive.style.display = "none";
    quizEnd.style.display = "block";

    const totalQuestions = quizQuestions.length;
    const finalPct = Math.round((quizScore / (totalQuestions * 10)) * 100);

    let badge = "🏆";
    let label = "Golden Hour Hero";
    if (finalPct < 35) {
      badge = "🔰";
      label = "Shield Rookie";
    } else if (finalPct < 65) {
      badge = "👁️";
      label = "Scam Spotter";
    } else if (finalPct < 85) {
      badge = "🛡️";
      label = "Digital Defender";
    } else if (finalPct < 95) {
      badge = "⚔️";
      label = "Cyber Guardian";
    }

    document.getElementById("quiz-badge-emoji").textContent = badge;
    document.getElementById("quiz-final-score").textContent = `${quizScore} Points (${finalPct}%)`;
    document.getElementById("quiz-final-label").textContent = `Badge Earned: ${label}`;

    // WhatsApp share link
    const shareText = encodeURIComponent(
      `I scored ${quizScore} points and earned the ${badge} ${label} badge on the ScamShield Cyber Safety Quiz! 🛡️ Test your scam radar here: https://scamshield.vercel.app`
    );
    document.getElementById("quiz-whatsapp-share").href = `https://wa.me/?text=${shareText}`;
  }

  document.getElementById("quiz-play-again-btn")?.addEventListener("click", () => {
    quizEnd.style.display = "none";
    quizSetup.style.display = "block";
  });

  // ── THREAT INTEL: Modus Operandi & Spotlight ───────────────────────────────
  async function loadIntel() {
    try {
      const res = await fetch("/api/intel");
      if (!res.ok) return;
      const data = await res.json();

      const intelGrid = document.getElementById("intel-grid");
      if (data.scam_trends && intelGrid) {
        intelGrid.innerHTML = "";
        data.scam_trends.forEach((item) => {
          const card = document.createElement("div");
          card.className = "intel-card";
          const title = item[`title_${currentLanguage}`] || item.title || "";
          const pattern = item[`pattern_${currentLanguage}`] || item.pattern || "";
          const realityCheck = item[`reality_check_${currentLanguage}`] || item.reality_check || "";
          const sourceTag = item.source ? `<div class="intel-source-tag">🏛️ ${item.source}</div>` : '';
          const statBadge = item.stat ? `<div class="intel-stat-badge">📊 <strong>Verified Impact:</strong> ${item.stat}</div>` : '';
          const caseBox = item.landmark_case ? `<div class="intel-case-box"><strong>🚨 Landmark Police Case:</strong> ${item.landmark_case}</div>` : '';
          card.innerHTML = `
            <div class="intel-meta-badges">
              <span class="intel-badge ${item.severity || "HIGH"}">${item.severity || "HIGH THREAT"}</span>
              ${sourceTag}
            </div>
            <div class="intel-title">${title}</div>
            <div class="intel-desc">${pattern}</div>
            ${statBadge}
            ${caseBox}
            <div class="intel-reality-box">
              <div class="intel-reality-title">🛡️ Official Defense Reality Check:</div>
              <p class="intel-reality-text">${realityCheck}</p>
            </div>
          `;
          intelGrid.appendChild(card);
        });
      }

      const goldenHourList = document.getElementById("golden-hour-list");
      if (data.golden_hour_steps && goldenHourList) {
        goldenHourList.innerHTML = "";
        data.golden_hour_steps.forEach((step) => {
          const li = document.createElement("li");
          const sTitle = step[`step_${currentLanguage}`] || step.step;
          const sDetail = step[`detail_${currentLanguage}`] || step.detail;
          li.innerHTML = `<strong>${sTitle}:</strong> ${sDetail}`;
          goldenHourList.appendChild(li);
        });
      }
    } catch (err) {
      console.warn("Could not load threat intel:", err);
    }
  }

  loadIntel();

  // ── COMMUNITY: Report a Scam & Check Database ──────────────────────────────
  const communityReportBtn = document.getElementById("community-report-btn");
  const reportSpinner = document.getElementById("report-spinner");
  const reportStatus = document.getElementById("report-status");

  communityReportBtn?.addEventListener("click", async () => {
    const scamType = document.getElementById("report-type").value;
    const value = document.getElementById("report-value").value.trim();
    const desc = document.getElementById("report-desc").value.trim();

    if (!value) {
      alert("Please enter a phone number, UPI ID, or URL to report.");
      return;
    }

    communityReportBtn.disabled = true;
    reportSpinner.style.display = "inline-block";
    reportStatus.style.display = "none";

    try {
      const res = await fetch("/api/community/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scam_type: scamType,
          value,
          description: desc,
          language: currentLanguage,
        }),
      });

      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "Submission failed");

      reportStatus.textContent = `✅ ${json.message || "Scam report recorded in the community database!"}`;
      reportStatus.className = "status-msg success";
      reportStatus.style.display = "block";
      document.getElementById("report-value").value = "";
      document.getElementById("report-desc").value = "";

      loadRecentCommunityReports();
    } catch (err) {
      reportStatus.textContent = `Error: ${err.message}`;
      reportStatus.className = "status-msg error";
      reportStatus.style.display = "block";
    } finally {
      communityReportBtn.disabled = false;
      reportSpinner.style.display = "none";
    }
  });

  const communityCheckBtn = document.getElementById("community-check-btn");
  const checkSpinner = document.getElementById("check-spinner");
  const checkResultCard = document.getElementById("community-check-result");

  communityCheckBtn?.addEventListener("click", async () => {
    const scamType = document.getElementById("check-type").value;
    const value = document.getElementById("check-value").value.trim();

    if (!value) {
      alert("Please enter a value to check.");
      return;
    }

    communityCheckBtn.disabled = true;
    checkSpinner.style.display = "inline-block";
    checkResultCard.style.display = "none";

    try {
      const res = await fetch(`/api/community/check?type=${scamType}&value=${encodeURIComponent(value)}`);
      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "Check failed");

      const d = json.data;
      checkResultCard.style.display = "block";

      const badge = document.getElementById("community-verdict");
      badge.textContent = d.found ? (d.reports_count > 5 ? "SCAM REPORTED" : "SUSPICIOUS") : "UNREPORTED / CLEAN";
      badge.className = `verdict-badge ${d.found ? (d.reports_count > 5 ? "SCAM" : "SUSPICIOUS") : "SAFE"}`;

      document.getElementById("community-report-count").textContent = d.reports_count || 0;
      document.getElementById("community-result-desc").textContent = d.description || "No complaints recorded.";
    } catch (err) {
      alert(`Community check error: ${err.message}`);
    } finally {
      communityCheckBtn.disabled = false;
      checkSpinner.style.display = "none";
    }
  });

  async function loadRecentCommunityReports() {
    const list = document.getElementById("community-feed-list");
    if (!list) return;

    try {
      const res = await fetch("/api/community/recent?limit=10");
      const json = await res.json();
      if (json.success && json.reports) {
        list.innerHTML = "";
        json.reports.forEach((r) => {
          const item = document.createElement("div");
          item.className = "feed-item";
          item.innerHTML = `
            <div class="feed-item-left">
              <span class="feed-type-pill">${(r.type || "phone").toUpperCase()}</span>
              <div>
                <strong style="font-family:var(--font-mono);font-size:0.9rem;">${r.masked_value}</strong>
                <p style="font-size:0.75rem;color:var(--text-muted);margin-top:2px;">${r.description || r.category || "Fraud reported"}</p>
              </div>
            </div>
            <div style="text-align:right;">
              <span class="feed-count-badge">🚨 ${r.reports_count} reports</span>
              <div style="font-size:0.7rem;color:var(--text-dim);margin-top:4px;">${new Date(r.last_reported || Date.now()).toLocaleDateString()}</div>
            </div>
          `;
          list.appendChild(item);
        });
      }
    } catch (e) {
      console.warn("Could not load community feed:", e);
    }
  }

  // ── RECOVERY WIZARD ────────────────────────────────────────────────────────
  window.wizardGoTo = function (stepNum) {
    for (let i = 1; i <= 5; i++) {
      document.getElementById(`wizard-step-${i}`)?.classList.toggle("active", i === stepNum);
      const dot = document.getElementById(`wizard-dot-${i}`);
      if (dot) {
        dot.classList.toggle("active", i === stepNum);
        dot.classList.toggle("completed", i < stepNum);
      }
    }

    if (stepNum === 4) generateActionPlan();
  };

  window.wizardReset = function () {
    wizardData = { time: "lt1", minutes: 30, bank: "", bankInfo: null, checkedActions: [] };
    wizardGoTo(1);
  };

  // Step 1: Time options
  document.querySelectorAll(".time-option").forEach((opt) => {
    opt.addEventListener("click", async () => {
      document.querySelectorAll(".time-option").forEach((o) => o.classList.remove("selected"));
      opt.classList.add("selected");

      const t = opt.getAttribute("data-time");
      wizardData.time = t;
      const mins = t === "lt1" ? 30 : (t === "1to3" ? 120 : (t === "3to24" ? 600 : 2000));
      wizardData.minutes = mins;

      try {
        const res = await fetch("/api/victim/status", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ minutes_elapsed: mins }),
        });
        const json = await res.json();
        if (json.success) {
          const s = json.data;
          const ind = document.getElementById("golden-hour-indicator");
          ind.innerHTML = `
            <div style="border-left:4px solid ${s.color};padding-left:12px;">
              <strong style="color:${s.color};font-size:1rem;">${s.badge}</strong>
              <p style="font-size:0.84rem;margin-top:4px;">${s.message}</p>
              <p style="font-size:0.78rem;color:var(--text-dim);margin-top:2px;">Recovery probability: <strong>${s.chance}</strong></p>
            </div>
          `;
          document.getElementById("wizard-next-1").disabled = false;
        }
      } catch (e) {
        console.warn(e);
      }
    });
  });

  document.getElementById("wizard-next-1")?.addEventListener("click", () => wizardGoTo(2));

  // Step 2: Bank Selection
  async function loadBankCatalog() {
    try {
      const res = await fetch("/api/victim/banks");
      const json = await res.json();
      if (json.success && json.banks) {
        bankCatalog = json.banks;
        const sel = document.getElementById("wizard-bank-select");
        sel.innerHTML = `<option value="">— Select Bank / App —</option>`;
        for (const [name, info] of Object.entries(bankCatalog)) {
          const opt = document.createElement("option");
          opt.value = name;
          opt.textContent = name;
          sel.appendChild(opt);
        }
      }
    } catch (e) {
      console.warn("Could not load banks catalog:", e);
    }
  }

  document.getElementById("wizard-bank-select")?.addEventListener("change", (e) => {
    const val = e.target.value;
    wizardData.bank = val;
    const info = bankCatalog[val];
    const box = document.getElementById("wizard-bank-info");

    if (info) {
      wizardData.bankInfo = info;
      document.getElementById("wizard-bank-name").textContent = val;
      document.getElementById("wizard-bank-hotline").textContent = info.fraud_helpline || info.toll_free;
      document.getElementById("wizard-bank-extra").textContent = `${info.sms_block ? info.sms_block + " • " : ""}${info.portal || ""}`;
      box.style.display = "flex";
      document.getElementById("wizard-next-2").disabled = false;
    } else {
      box.style.display = "none";
      document.getElementById("wizard-next-2").disabled = true;
    }
  });

  document.getElementById("wizard-next-2")?.addEventListener("click", () => wizardGoTo(3));

  // Step 3: Checkboxes
  document.getElementById("wizard-next-3")?.addEventListener("click", () => {
    wizardData.checkedActions = [];
    if (document.getElementById("chk-money")?.checked) wizardData.checkedActions.push("money");
    if (document.getElementById("chk-otp")?.checked) wizardData.checkedActions.push("otp");
    if (document.getElementById("chk-app")?.checked) wizardData.checkedActions.push("app");
    if (document.getElementById("chk-card")?.checked) wizardData.checkedActions.push("card");
    if (document.getElementById("chk-aadhaar")?.checked) wizardData.checkedActions.push("aadhaar");
    wizardGoTo(4);
  });

  function generateActionPlan() {
    const container = document.getElementById("wizard-action-list");
    if (!container) return;
    container.innerHTML = "";

    const acts = [];
    acts.push({
      icon: "🚨",
      title: "Call 1930 Helpline IMMEDIATELY",
      desc: "Report to National Cyber Crime Helpline (MHA I4C) with transaction UTR number to trigger freeze on scammer's beneficiary account.",
    });

    if (wizardData.bankInfo) {
      acts.push({
        icon: "🏦",
        title: `Contact ${wizardData.bank} Fraud Monitoring Desk`,
        desc: `Call ${wizardData.bankInfo.fraud_helpline || wizardData.bankInfo.toll_free}. Request an immediate debit freeze and dispute registration.`,
      });
    }

    if (wizardData.checkedActions.includes("card")) {
      acts.push({
        icon: "💳",
        title: "Block Compromised Debit / Credit Card",
        desc: "Open your bank mobile app and block the card immediately, or send the SMS block code.",
      });
    }

    if (wizardData.checkedActions.includes("app")) {
      acts.push({
        icon: "📲",
        title: "Disconnect Internet & Uninstall Remote Apps",
        desc: "Turn off Wi-Fi and Mobile Data immediately. Go to Settings > Apps and uninstall AnyDesk, TeamViewer, RustDesk, or recently downloaded APKs.",
      });
    }

    if (wizardData.checkedActions.includes("otp")) {
      acts.push({
        icon: "🔑",
        title: "Reset Net Banking & UPI Passwords",
        desc: "From a different, clean device, change your Internet Banking login password and UPI PIN.",
      });
    }

    acts.push({
      icon: "🏛️",
      title: "File Formal Complaint at cybercrime.gov.in",
      desc: "Register a complaint with all transaction receipts, chats, and phone numbers to receive an official Acknowledgement Number.",
    });

    acts.forEach((a) => {
      const item = document.createElement("div");
      item.className = "wizard-action-item";
      item.innerHTML = `
        <div class="action-icon">${a.icon}</div>
        <div class="action-text">
          <strong>${a.title}</strong>
          <p>${a.desc}</p>
        </div>
      `;
      container.appendChild(item);
    });
  }

  // Step 5: AI FIR Draft Generator
  const generateFirBtn = document.getElementById("generate-fir-btn");
  const firSpinner = document.getElementById("fir-spinner");
  const firDraftBox = document.getElementById("fir-draft-box");

  generateFirBtn?.addEventListener("click", async () => {
    generateFirBtn.disabled = true;
    firSpinner.style.display = "inline-block";
    firDraftBox.textContent = "Synthesizing formal legal complaint draft with AI...";

    const prompt = `Write a formal cybercrime police complaint / FIR draft for a victim of digital fraud in India.
Details:
- Bank / App: ${wizardData.bank || "UPI / Net Banking"}
- Actions involved: ${wizardData.checkedActions.join(", ") || "Unauthorized transaction"}
- Approximate time elapsed: ${wizardData.minutes} minutes
Include:
1. Formal subject line to the Cyber Crime Police Station / cybercrime.gov.in
2. Clear facts section with placeholders for [Name], [Account Number], [Transaction ID/UTR], [Date], [Amount Lost], [Scammer Phone Number]
3. Reference to relevant sections of Information Technology Act 2000 (Sec 66C, 66D) and IPC/BNS
4. Urgent request to issue freezing notice to beneficiary bank under Sec 91 CrPC
5. Complainant declaration.
Language: Professional English.`;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [{ role: "user", content: prompt }],
          language: "en",
        }),
      });

      const json = await res.json();
      if (!res.ok || !json.success) throw new Error(json.error || "Draft generation failed");
      firDraftBox.textContent = json.reply;
    } catch (err) {
      firDraftBox.textContent = `Error generating draft: ${err.message}`;
    } finally {
      generateFirBtn.disabled = false;
      firSpinner.style.display = "none";
    }
  });

  document.getElementById("copy-fir-btn")?.addEventListener("click", () => {
    navigator.clipboard.writeText(firDraftBox.textContent).then(() => {
      alert("FIR Draft copied to clipboard! Paste directly into your cyber complaint.");
    });
  });

  // ── HISTORY TAB ────────────────────────────────────────────────────────────
  function renderHistoryTable() {
    const list = getHistory();
    const total = list.length;
    const safe = list.filter((i) => i.verdict === "SAFE").length;
    const susp = list.filter((i) => i.verdict === "SUSPICIOUS").length;
    const scam = list.filter((i) => i.verdict === "SCAM").length;

    document.getElementById("hist-total").textContent = total;
    document.getElementById("hist-safe").textContent = safe;
    document.getElementById("hist-suspicious").textContent = susp;
    document.getElementById("hist-scam").textContent = scam;

    const tbody = document.getElementById("history-tbody");
    const empty = document.getElementById("history-empty");
    const table = document.getElementById("history-table");

    if (total === 0) {
      empty.style.display = "block";
      table.style.display = "none";
      return;
    }

    empty.style.display = "none";
    table.style.display = "table";
    tbody.innerHTML = "";

    const typeFilter = document.getElementById("hist-filter-type")?.value || "";
    const verdictFilter = document.getElementById("hist-filter-verdict")?.value || "";

    const filtered = list.filter((item) => {
      if (typeFilter && item.type !== typeFilter) return false;
      if (verdictFilter && item.verdict !== verdictFilter) return false;
      return true;
    });

    filtered.forEach((item) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td style="font-family:var(--font-mono);font-size:0.75rem;">${item.date}</td>
        <td><span class="history-type-pill">${item.type.toUpperCase()}</span></td>
        <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${item.preview}</td>
        <td><span class="verdict-badge ${item.verdict}" style="font-size:0.7rem;padding:2px 8px;">${item.verdict}</span></td>
        <td style="font-family:var(--font-mono);font-weight:700;">${item.score}/100</td>
        <td style="font-size:0.78rem;color:var(--text-muted);">${item.summary}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("hist-filter-type")?.addEventListener("change", renderHistoryTable);
  document.getElementById("hist-filter-verdict")?.addEventListener("change", renderHistoryTable);

  document.getElementById("clear-history-btn")?.addEventListener("click", () => {
    if (confirm("Are you sure you want to clear your local scan history?")) {
      localStorage.removeItem(STORAGE_KEY);
      renderHistoryTable();
    }
  });

  document.getElementById("export-history-btn")?.addEventListener("click", () => {
    const list = getHistory();
    if (!list.length) {
      alert("No scan history to export.");
      return;
    }
    const reportText = `SCAMSHIELD CYBER-SCAN AUDIT REPORT
Generated: ${new Date().toLocaleString()}
Total Scans: ${list.length}

${list
  .map(
    (item, idx) => `[${idx + 1}] ${item.date}
Type: ${item.type.toUpperCase()}
Input: ${item.preview}
Verdict: ${item.verdict} (Risk: ${item.score}/100)
Summary: ${item.summary}
--------------------------------------------------`
  )
  .join("\n\n")}`;

    const blob = new Blob([reportText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ScamShield_Audit_Report_${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  });

  // ── SECURITY HYGIENE ASSESSMENT ────────────────────────────────────────────
  window.toggleHygiene = function (elem) {
    const chk = elem.querySelector("input[type=checkbox]");
    if (chk) {
      chk.checked = !chk.checked;
      elem.classList.toggle("checked", chk.checked);
      recalculateHygiene();
    }
  };

  async function recalculateHygiene() {
    const checkedBoxes = document.querySelectorAll(".hygiene-item input[type=checkbox]:checked");
    const checkedIds = Array.from(checkedBoxes).map((c) => c.id);

    try {
      const res = await fetch("/api/hygiene/score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ checked_ids: checkedIds }),
      });
      const json = await res.json();
      if (json.success && json.data) {
        const d = json.data;
        document.getElementById("hygiene-score-number").textContent = d.score;
        document.getElementById("hygiene-score-grade").textContent = d.grade;

        const circle = document.getElementById("score-circle");
        circle.style.borderColor = d.color;
        circle.style.boxShadow = `0 0 20px ${d.color}40`;

        const tipsBox = document.getElementById("hygiene-tips");
        tipsBox.innerHTML = `<h4>⚠️ Priority Improvements</h4>`;
        if (d.recommendations && d.recommendations.length > 0) {
          d.recommendations.forEach((r) => {
            const div = document.createElement("div");
            div.style.marginBottom = "8px";
            div.innerHTML = `<strong style="font-size:0.8rem;color:var(--text-main);">${r.title}</strong><p style="font-size:0.75rem;color:var(--text-muted);">${r.tip}</p>`;
            tipsBox.appendChild(div);
          });
        } else {
          tipsBox.innerHTML += `<p style="font-size:0.8rem;color:var(--safe-green);">All critical security checkpoints satisfied!</p>`;
        }
      }
    } catch (e) {
      console.warn("Hygiene score recalculation error:", e);
    }
  }

  document.getElementById("share-hygiene-score")?.addEventListener("click", () => {
    const score = document.getElementById("hygiene-score-number").textContent;
    const grade = document.getElementById("hygiene-score-grade").textContent;
    const text = encodeURIComponent(
      `My Digital Defense Hygiene rating on ScamShield is ${score}/100 (Grade ${grade})! 🛡️ Check your cyber safety posture at https://scamshield.vercel.app`
    );
    window.open(`https://wa.me/?text=${text}`, "_blank");
  });

  // ── FAMILY ALERT DISPATCH ──────────────────────────────────────────────────
  function updateAlertPreview(data) {
    if (!data) return;
    const text = `🚨 [SCAMSHIELD FRAUD ADVISORY]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verdict: ${data.verdict}
Risk Score: ${data.risk_score} / 100
Summary: ${data.summary}

⚠️ Detected Flags:
${(data.red_flags || []).map((f) => `• ${f}`).join("\n")}

🛡️ Required Action:
${(data.action_items || [data.advice] || []).map((a) => `• ${a}`).join("\n")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
National Cyber Crime Helpline: 1930
Report Portal: https://cybercrime.gov.in`;
    const previewElem = document.getElementById("alert-preview-text");
    if (previewElem) previewElem.textContent = text;
  }

  // Channel Tabs in Family Alert
  document.querySelectorAll(".channel-tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const ch = btn.getAttribute("data-channel");
      document.querySelectorAll(".channel-tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".channel-panel").forEach((p) => p.classList.toggle("active", p.id === `channel-${ch}`));
    });
  });

  document.getElementById("send-discord-btn")?.addEventListener("click", async () => {
    const webhook = document.getElementById("discord-webhook")?.value.trim();
    if (!currentAnalysis) {
      showAlertStatus("Please scan a message or screenshot first before dispatching an alert.", "error");
      return;
    }

    try {
      const res = await fetch("/api/alert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          verdict: currentAnalysis.verdict,
          risk_score: currentAnalysis.risk_score,
          summary: currentAnalysis.summary,
          red_flags: currentAnalysis.red_flags || [],
          action_items: currentAnalysis.action_items || [],
          language: currentLanguage,
          webhook_url: webhook || null,
        }),
      });

      const json = await res.json();
      if (json.success) {
        showAlertStatus(json.message || "Alert dispatched to Discord successfully!", "success");
      } else {
        showAlertStatus(json.message || "Discord webhook not configured. Copied to clipboard!", "error");
        navigator.clipboard.writeText(document.getElementById("alert-preview-text")?.textContent || "");
      }
    } catch (err) {
      showAlertStatus(`Error: ${err.message}`, "error");
    }
  });

  document.getElementById("send-telegram-btn")?.addEventListener("click", async () => {
    const token = document.getElementById("telegram-bot-token")?.value.trim();
    const chatId = document.getElementById("telegram-chat-id")?.value.trim();
    const text = document.getElementById("alert-preview-text")?.textContent || "";

    if (!token || !chatId) {
      showAlertStatus("Please enter both Telegram Bot Token and Chat ID.", "error");
      return;
    }

    try {
      const url = `https://api.telegram.org/bot${token}/sendMessage`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chat_id: chatId, text }),
      });
      const data = await res.json();
      if (data.ok) {
        showAlertStatus("Telegram alert dispatched to family group!", "success");
      } else {
        showAlertStatus(`Telegram Error: ${data.description}`, "error");
      }
    } catch (err) {
      showAlertStatus(`Telegram dispatch error: ${err.message}`, "error");
    }
  });

  document.getElementById("copy-clipboard-btn")?.addEventListener("click", () => {
    const text = document.getElementById("alert-preview-text")?.textContent || "";
    navigator.clipboard.writeText(text).then(() => {
      showAlertStatus("Security alert copied! Paste directly into WhatsApp or SMS.", "success");
    });
  });

  function showAlertStatus(msg, type) {
    const el = document.getElementById("alert-status-msg");
    if (!el) return;
    el.textContent = msg;
    el.className = `status-msg ${type}`;
    el.style.display = "block";
    setTimeout(() => (el.style.display = "none"), 5000);
  }

  // ── Initialize App ─────────────────────────────────────────────────────────
  initLanguages();
});
