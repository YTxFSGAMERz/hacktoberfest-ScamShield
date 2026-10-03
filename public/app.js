// ScamShield — Frontend Client Application
document.addEventListener("DOMContentLoaded", () => {
  // ── State ─────────────────────────────────────────────────────────────
  let currentFile = null;
  let currentBase64 = null;
  let currentAnalysis = null;
  let currentLanguage = "en";
  let chatHistory = [];

  // ── Localization Dictionaries ──────────────────────────────────────────
  const I18N = {
    en: {
      tagline: "Cyber-Fraud Intelligence & Scam Detection — Powered by Gemma 4",
      lbl_samples: "Test Vectors",
      lbl_languages: "Languages (EN/HI/GU)",
      lbl_helpline: "Cyber Cell Ready",
      lbl_vision: "Vision Reasoning",
      tab_scanner: "Scanner",
      tab_chat: "AI Assistant",
      tab_intel: "Threat Intel",
      tab_emergency: "Helplines",
      tab_alerts: "Family Alert",
      genuine_samples: "✅ Genuine / Legitimate:",
      scam_samples: "🚨 Fraudulent / Threats:",
      upload_title: "📤 Upload Suspicious Screenshot",
      upload_desc: "Drop an SMS, WhatsApp screenshot, fake UPI QR, bank debit alert, or app prompt.",
      drag_drop: 'Drag & drop image here or <span class="browse-link">browse</span>',
      sender_header: "TRAI / SMS Header (Optional):",
      analyze_btn: "🛡️ Analyze with Gemma 4",
      awaiting_title: "Awaiting Screenshot",
      awaiting_desc: "Upload an image or pick a test sample above to execute real-time Gemma 4 reasoning.",
      summary_title: "Executive Summary",
      red_flags_title: "Detected Signals & Red Flags",
      action_plan_title: "Recommended Actions",
    },
    hi: {
      tagline: "साइबर-धोखाधड़ी रोकथाम एवं स्कैम डिटेक्शन — Gemma 4 द्वारा संचालित",
      lbl_samples: "परीक्षण नमूने",
      lbl_languages: "भाषाएं (अंग्रेजी/हिंदी/गुजराती)",
      lbl_helpline: "साइबर सेल तैयार",
      lbl_vision: "विजन रीजनिंग",
      tab_scanner: "स्कैनर",
      tab_chat: "एआई सहायक",
      tab_intel: "खतरा ज्ञान",
      tab_emergency: "हेल्पलाइन",
      tab_alerts: "परिवार अलर्ट",
      genuine_samples: "✅ असली / प्रमाणित संदेश:",
      scam_samples: "🚨 फर्जी / धोखाधड़ी संदेश:",
      upload_title: "📤 संदिग्ध स्क्रीनशॉट अपलोड करें",
      upload_desc: "एसएमएस, व्हाट्सएप चैट, फर्जी यूपीआई स्क्रीन, या बैंक संदेश का स्क्रीनशॉट दें।",
      drag_drop: 'यहाँ स्क्रीनशॉट खींचें या <span class="browse-link">फ़ाइल चुनें</span>',
      sender_header: "TRAI / SMS हेडर (वैकल्पिक):",
      analyze_btn: "🛡️ Gemma 4 से जांचें",
      awaiting_title: "स्क्रीनशॉट की प्रतीक्षा है",
      awaiting_desc: "छवि अपलोड करें या ऊपर दिए गए नमूनों में से एक चुनें।",
      summary_title: "मुख्य सारांश",
      red_flags_title: "पहचाने गए खतरे और संकेत",
      action_plan_title: "सुरक्षा निर्देश एवं कदम",
    },
    gu: {
      tagline: "સાયબર-છેતરપિંડી સંરક્ષણ અને સ્કેમ તપાસ — Gemma 4 દ્વારા સંચાલિત",
      lbl_samples: "ટેસ્ટ સેમ્પલ",
      lbl_languages: "ભાષાઓ (EN/HI/GU)",
      lbl_helpline: "સાયબર સેલ તૈયાર",
      lbl_vision: "વિઝન રીઝનિંગ",
      tab_scanner: "સ્કેનર",
      tab_chat: "AI સહાયક",
      tab_intel: "જોખમ માહિતી",
      tab_emergency: "હેલ્પલાઇન",
      tab_alerts: "કુટુંબ અલર્ટ",
      genuine_samples: "✅ અસલી / માન્ય સંદેશાઓ:",
      scam_samples: "🚨 છેતરપિંડી / જોખમી સંદેશાઓ:",
      upload_title: "📤 શંકાસ્પદ સ્ક્રીનશોટ અપલોડ કરો",
      upload_desc: "SMS, WhatsApp સ્ક્રીનશોટ, નકલી UPI QR અથવા બેંક મેસેજ અહીં મૂકો.",
      drag_drop: 'અહીં છબી ખેંચો અથવા <span class="browse-link">બ્રાઉઝ કરો</span>',
      sender_header: "TRAI / SMS હેડર (વૈકલ્પિક):",
      analyze_btn: "🛡️ Gemma 4 વડે તપાસો",
      awaiting_title: "સ્ક્રીનશોટની રાહ જોવાય છે",
      awaiting_desc: "છબી અપલોડ કરો અથવા ઉપરના નમૂનાઓમાંથી એક પસંદ કરો.",
      summary_title: "મુખ્ય સારાંશ",
      red_flags_title: "શોધાયેલા જોખમી સંકેતો",
      action_plan_title: "સુરક્ષા માટે ભલામણ કરેલ પગલાં",
    }
  };

  // ── DOM Elements ───────────────────────────────────────────────────────
  const langSelect = document.getElementById("lang-select");
  const tabBtns = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

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
  const legitBanner = document.getElementById("legit-banner");
  const summaryText = document.getElementById("summary-text");
  const redFlagsList = document.getElementById("red-flags-list");
  const actionList = document.getElementById("action-list");
  const reasoningText = document.getElementById("reasoning-text");

  const sendToChatBtn = document.getElementById("send-to-chat-btn");
  const sendToAlertBtn = document.getElementById("send-to-alert-btn");

  const chatThread = document.getElementById("chat-thread");
  const chatInput = document.getElementById("chat-input");
  const chatSendBtn = document.getElementById("chat-send-btn");
  const scanContextBadge = document.getElementById("scan-context-badge");

  const intelGrid = document.getElementById("intel-grid");
  const goldenHourList = document.getElementById("golden-hour-list");

  const discordWebhook = document.getElementById("discord-webhook");
  const sendDiscordBtn = document.getElementById("send-discord-btn");
  const copyClipboardBtn = document.getElementById("copy-clipboard-btn");
  const alertStatusMsg = document.getElementById("alert-status-msg");
  const alertPreviewText = document.getElementById("alert-preview-text");

  // ── Language Toggle ────────────────────────────────────────────────────
  function applyLanguage(lang) {
    currentLanguage = lang;
    const t = I18N[lang] || I18N.en;

    document.getElementById("tagline-text").textContent = t.tagline;
    document.getElementById("lbl-samples").textContent = t.lbl_samples;
    document.getElementById("lbl-languages").textContent = t.lbl_languages;
    document.getElementById("lbl-helpline").textContent = t.lbl_helpline;
    document.getElementById("lbl-vision").textContent = t.lbl_vision;

    document.getElementById("tab-lbl-scanner").textContent = t.tab_scanner;
    document.getElementById("tab-lbl-chat").textContent = t.tab_chat;
    document.getElementById("tab-lbl-intel").textContent = t.tab_intel;
    document.getElementById("tab-lbl-emergency").textContent = t.tab_emergency;
    document.getElementById("tab-lbl-alerts").textContent = t.tab_alerts;

    document.getElementById("lbl-genuine-samples").textContent = t.genuine_samples;
    document.getElementById("lbl-scam-samples").textContent = t.scam_samples;
    document.getElementById("lbl-upload-title").textContent = t.upload_title;
    document.getElementById("lbl-upload-desc").textContent = t.upload_desc;
    document.getElementById("lbl-drag-drop").innerHTML = t.drag_drop;
    document.getElementById("lbl-sender-header").textContent = t.sender_header;
    document.getElementById("lbl-analyze-btn").textContent = t.analyze_btn;

    document.getElementById("lbl-awaiting-title").textContent = t.awaiting_title;
    document.getElementById("lbl-awaiting-desc").textContent = t.awaiting_desc;
    document.getElementById("lbl-summary").textContent = t.summary_title;
    document.getElementById("lbl-red-flags").textContent = t.red_flags_title;
    document.getElementById("lbl-action-plan").textContent = t.action_plan_title;
  }

  langSelect.addEventListener("change", (e) => {
    applyLanguage(e.target.value);
  });

  // ── Tab Navigation ─────────────────────────────────────────────────────
  function switchTab(targetTab) {
    tabBtns.forEach(btn => {
      const isActive = btn.getAttribute("data-tab") === targetTab;
      btn.classList.toggle("active", isActive);
      btn.setAttribute("aria-selected", isActive);
    });

    tabContents.forEach(content => {
      content.classList.toggle("active", content.id === `tab-${targetTab}`);
    });
  }

  tabBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      switchTab(btn.getAttribute("data-tab"));
    });
  });

  // ── Drag & Drop / File Handling ─────────────────────────────────────────
  dropZone.addEventListener("click", (e) => {
    if (e.target !== removeImgBtn) {
      fileInput.click();
    }
  });

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      handleFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length) {
      handleFile(e.target.files[0]);
    }
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
    document.querySelectorAll(".sample-chip").forEach(c => c.classList.remove("active"));
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
      if (autoAnalyze) {
        runAnalysis();
      }
    };
    reader.readAsDataURL(file);
  }

  // ── Sample Chips Quick Test ────────────────────────────────────────────
  document.querySelectorAll(".sample-chip").forEach(chip => {
    chip.addEventListener("click", async () => {
      const fileName = chip.getAttribute("data-file");
      document.querySelectorAll(".sample-chip").forEach(c => c.classList.remove("active"));
      chip.classList.add("active");

      // Auto-populate sender header if genuine sample
      if (fileName.includes("login_otp")) {
        senderInput.value = "VK-AMZNOT";
      } else if (fileName.includes("bank_alert")) {
        senderInput.value = "AD-HDFCBK";
      } else if (fileName.includes("swiggy")) {
        senderInput.value = "SWIGGY";
      } else if (fileName.includes("irctc")) {
        senderInput.value = "IRCTC";
      } else {
        senderInput.value = "";
      }

      try {
        let res = await fetch(`/samples/${fileName}`);
        if (!res.ok) {
          res = await fetch(`/api/sample/${fileName}`);
        }
        if (!res.ok) throw new Error("Failed to load sample image");
        const blob = await res.blob();
        handleFile(new File([blob], fileName, { type: "image/png" }), true);
      } catch (err) {
        console.error("Sample load error:", err);
      }
    });
  });

  // ── Run Analysis ───────────────────────────────────────────────────────
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
      if (!res.ok || !json.success) {
        throw new Error(json.error || "Analysis failed");
      }

      renderVerdict(json.data);
    } catch (err) {
      alert(`Analysis error: ${err.message}`);
      emptyState.style.display = "flex";
    } finally {
      analyzeBtn.disabled = false;
      analyzeSpinner.style.display = "none";
    }
  }

  analyzeBtn.addEventListener("click", runAnalysis);

  // ── Render Verdict Display ─────────────────────────────────────────────
  function renderVerdict(data) {
    currentAnalysis = data;
    emptyState.style.display = "none";
    verdictContainer.style.display = "block";

    const verdict = data.verdict || "SAFE";
    const score = data.risk_score || 0;

    // Badge styling
    verdictBadge.textContent = verdict;
    verdictBadge.className = `verdict-badge ${verdict}`;

    // Score & meter
    chartScore.textContent = score;
    const chartWrap = document.getElementById("circular-chart");
    if (verdict === "SAFE") {
      chartWrap.style.borderColor = "var(--safe-green)";
      chartWrap.style.boxShadow = "0 0 16px var(--safe-glow)";
      legitBanner.style.display = "flex";
    } else if (verdict === "SUSPICIOUS") {
      chartWrap.style.borderColor = "var(--warning-amber)";
      chartWrap.style.boxShadow = "0 0 16px var(--warning-glow)";
      legitBanner.style.display = "none";
    } else {
      chartWrap.style.borderColor = "var(--scam-red)";
      chartWrap.style.boxShadow = "0 0 20px var(--scam-glow)";
      legitBanner.style.display = "none";
    }

    // Summary
    summaryText.textContent = data.summary || "No summary provided.";

    // Red flags
    redFlagsList.innerHTML = "";
    if (data.red_flags && data.red_flags.length > 0) {
      document.getElementById("red-flags-box").style.display = "block";
      data.red_flags.forEach(flag => {
        const li = document.createElement("li");
        li.textContent = `⚠️ ${flag}`;
        redFlagsList.appendChild(li);
      });
    } else {
      document.getElementById("red-flags-box").style.display = "none";
    }

    // Actions checklist
    actionList.innerHTML = "";
    const items = data.action_items || [data.advice] || [];
    items.forEach(act => {
      const li = document.createElement("li");
      li.textContent = `🛡️ ${act}`;
      actionList.appendChild(li);
    });

    // Model reasoning
    reasoningText.textContent = data.reasoning || data.details || "Direct model response verified.";

    // Update alert preview
    updateAlertPreview(data);

    // Update chat scan context badge
    scanContextBadge.style.display = "inline-flex";
  }

  // ── Buttons to route to Chat / Alert ───────────────────────────────────
  sendToChatBtn.addEventListener("click", () => {
    switchTab("chat");
    if (currentAnalysis) {
      chatInput.value = `Can you explain why this screenshot was marked as ${currentAnalysis.verdict}?`;
      chatInput.focus();
    }
  });

  sendToAlertBtn.addEventListener("click", () => {
    switchTab("alerts");
  });

  // ── AI Safety Chat ─────────────────────────────────────────────────────
  async function sendChatMessage(userText) {
    if (!userText.trim()) return;

    // Append user bubble
    appendBubble("user", userText);
    chatInput.value = "";
    chatHistory.push({ role: "user", content: userText });

    // Append bot placeholder
    const botBubble = appendBubble("bot", "Analyzing safety vectors...", true);

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
      if (!res.ok || !json.success) {
        throw new Error(json.error || "Chat failed");
      }

      botBubble.querySelector(".bubble-body p").textContent = json.reply;
      chatHistory.push({ role: "assistant", content: json.reply });
    } catch (err) {
      botBubble.querySelector(".bubble-body p").textContent = `Error: ${err.message}`;
    }
  }

  function appendBubble(role, text, isPending = false) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role === "user" ? "user-bubble" : "bot-bubble"}`;
    bubble.innerHTML = `
      <div class="bubble-avatar">${role === "user" ? "👤" : "🛡️"}</div>
      <div class="bubble-body">
        <p>${text}</p>
      </div>
    `;
    chatThread.appendChild(bubble);
    chatThread.scrollTop = chatThread.scrollHeight;
    return bubble;
  }

  chatSendBtn.addEventListener("click", () => {
    sendChatMessage(chatInput.value);
  });

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      sendChatMessage(chatInput.value);
    }
  });

  document.querySelectorAll(".starter-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      sendChatMessage(chip.getAttribute("data-prompt"));
    });
  });

  // ── Threat Intel & Emergency Load ──────────────────────────────────────
  async function loadIntel() {
    try {
      const res = await fetch("/api/intel");
      if (!res.ok) return;
      const data = await res.json();

      // Render scam trends
      if (data.scam_trends) {
        intelGrid.innerHTML = "";
        data.scam_trends.forEach(item => {
          const card = document.createElement("div");
          card.className = "intel-card";
          const title = item[`title_${currentLanguage}`] || item.title || "";
          const pattern = item[`pattern_${currentLanguage}`] || item.pattern || item.modus_operandi || "";
          const realityCheck = item[`reality_check_${currentLanguage}`] || item.reality_check || item.defense || "";
          card.innerHTML = `
            <span class="intel-badge ${item.severity || 'HIGH'}">${item.severity || "HIGH THREAT"}</span>
            <div class="intel-title">${title}</div>
            <div class="intel-desc">${pattern}</div>
            <div class="intel-section-title" style="margin-top:10px; color:#38BDF8;">🛡️ Official Reality Check:</div>
            <p style="font-size:0.82rem; color:var(--safe-green); margin-top:4px; line-height:1.4;">${realityCheck}</p>
          `;
          intelGrid.appendChild(card);
        });
      }

      // Render Golden Hour
      if (data.golden_hour_steps) {
        goldenHourList.innerHTML = "";
        data.golden_hour_steps.forEach(step => {
          const li = document.createElement("li");
          li.innerHTML = `<strong>${step.step}:</strong> ${step.action} <em>(${step.urgency})</em>`;
          goldenHourList.appendChild(li);
        });
      }
    } catch (err) {
      console.warn("Could not load threat intel:", err);
    }
  }

  loadIntel();

  // ── Family Alert Center ────────────────────────────────────────────────
  function updateAlertPreview(data) {
    if (!data) return;
    const text = `🚨 [SCAMSHIELD FRAUD ADVISORY]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Verdict: ${data.verdict}
Risk Score: ${data.risk_score} / 100
Summary: ${data.summary}

⚠️ Detected Flags:
${(data.red_flags || []).map(f => `• ${f}`).join("\n")}

🛡️ Required Action:
${(data.action_items || []).map(a => `• ${a}`).join("\n")}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
National Cyber Crime Helpline: 1930
Report Portal: https://cybercrime.gov.in`;
    alertPreviewText.textContent = text;
  }

  sendDiscordBtn.addEventListener("click", async () => {
    const webhook = discordWebhook.value.trim();
    if (!currentAnalysis) {
      showStatus("Please scan a screenshot first before sending an alert.", "error");
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
        showStatus(json.message || "Alert dispatched to Discord successfully!", "success");
      } else {
        showStatus(json.message || "Discord webhook not configured. Alert copied to clipboard!", "error");
        navigator.clipboard.writeText(alertPreviewText.textContent);
      }
    } catch (err) {
      showStatus(`Error: ${err.message}`, "error");
    }
  });

  copyClipboardBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(alertPreviewText.textContent).then(() => {
      showStatus("Security alert copied to clipboard! Paste directly into WhatsApp or SMS.", "success");
    });
  });

  function showStatus(msg, type) {
    alertStatusMsg.textContent = msg;
    alertStatusMsg.className = `status-msg ${type}`;
    alertStatusMsg.style.display = "block";
    setTimeout(() => {
      alertStatusMsg.style.display = "none";
    }, 5000);
  }
});
