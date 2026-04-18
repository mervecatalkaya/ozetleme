/**
 * Meeting Assistant - Frontend JavaScript
 * =========================================
 * Dosya yükleme, form gönderimi, ilerleme göstergesi
 * ve sonuç sekmeleri yönetimi.
 */

document.addEventListener("DOMContentLoaded", () => {
    // ─── DOM Elementleri ──────────────────────────────────────────────────────
    const uploadForm = document.getElementById("upload-form");
    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("audio-file-input");
    const fileInfo = document.getElementById("file-info");
    const fileName = document.getElementById("file-name");
    const fileSize = document.getElementById("file-size");
    const removeFileBtn = document.getElementById("remove-file-btn");
    const submitBtn = document.getElementById("submit-btn");
    const btnText = submitBtn.querySelector(".btn-text");
    const btnLoader = submitBtn.querySelector(".btn-loader");

    const uploadSection = document.getElementById("upload-section");
    const progressSection = document.getElementById("progress-section");
    const errorSection = document.getElementById("error-section");
    const errorMessage = document.getElementById("error-message");
    const errorDismissBtn = document.getElementById("error-dismiss-btn");
    const resultsSection = document.getElementById("results-section");
    const resultsFilename = document.getElementById("results-filename");

    const transcriptContent = document.getElementById("transcript-content");
    const summaryContent = document.getElementById("summary-content");
    const tasksContent = document.getElementById("tasks-content");
    const taskCountBadge = document.getElementById("task-count-badge");
    const newUploadBtn = document.getElementById("new-upload-btn");

    const progressBarFill = document.getElementById("progress-bar-fill");



    // ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────

    /**
     * Dosya boyutunu okunabilir formata çevir.
     */
    function formatFileSize(bytes) {
        if (bytes < 1024) return bytes + " B";
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
        return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    }

    /**
     * Dosya uzantısının desteklenip desteklenmediğini kontrol et.
     */
    function isAllowedFile(filename) {
        const ext = filename.split(".").pop().toLowerCase();
        return ["mp3", "wav", "m4a", "ogg"].includes(ext);
    }

    /**
     * Bir bölümü gizle.
     */
    function hideSection(section) {
        section.style.display = "none";
    }

    /**
     * Bir bölümü göster.
     */
    function showSection(section) {
        section.style.display = "block";
    }


    // ─── Drag & Drop ─────────────────────────────────────────────────────────

    uploadZone.addEventListener("click", () => fileInput.click());

    uploadZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        uploadZone.classList.add("drag-over");
    });

    uploadZone.addEventListener("dragleave", (e) => {
        e.preventDefault();
        uploadZone.classList.remove("drag-over");
    });

    uploadZone.addEventListener("drop", (e) => {
        e.preventDefault();
        uploadZone.classList.remove("drag-over");

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });


    // ─── Dosya Seçimi ─────────────────────────────────────────────────────────

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0]);
        }
    });

    /**
     * Seçilen dosyayı işle ve arayüzü güncelle.
     */
    function handleFileSelect(file) {
        // Format kontrolü
        if (!isAllowedFile(file.name)) {
            showError("Desteklenmeyen dosya formatı. Lütfen MP3, WAV, M4A veya OGG dosyası seçin.");
            return;
        }

        // Boyut kontrolü (50 MB)
        if (file.size > 50 * 1024 * 1024) {
            showError("Dosya boyutu 50 MB'dan büyük olamaz.");
            return;
        }

        // Dosya input'a ata (drag & drop durumu için)
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;

        // Arayüzü güncelle
        fileName.textContent = file.name;
        fileSize.textContent = formatFileSize(file.size);
        fileInfo.style.display = "flex";
        submitBtn.disabled = false;

        // Hata varsa temizle
        hideSection(errorSection);
    }

    /**
     * Seçilen dosyayı kaldır.
     */
    removeFileBtn.addEventListener("click", () => {
        fileInput.value = "";
        fileInfo.style.display = "none";
        submitBtn.disabled = true;
    });



    // ─── İlerleme Göstergesi ──────────────────────────────────────────────────

    const progressSteps = {
        upload: document.querySelector("#step-upload .step-indicator"),
        transcribe: document.querySelector("#step-transcribe .step-indicator"),
        summarize: document.querySelector("#step-summarize .step-indicator"),
        tasks: document.querySelector("#step-tasks .step-indicator"),
    };

    const progressStepElements = {
        upload: document.getElementById("step-upload"),
        transcribe: document.getElementById("step-transcribe"),
        summarize: document.getElementById("step-summarize"),
        tasks: document.getElementById("step-tasks"),
    };

    /**
     * İlerleme adımını güncelle (simülasyon).
     */
    function setProgressStep(stepName, status) {
        const indicator = progressSteps[stepName];
        const stepEl = progressStepElements[stepName];

        if (!indicator || !stepEl) return;

        // Önceki durumları temizle
        indicator.classList.remove("active", "done");
        stepEl.classList.remove("active", "done");

        if (status === "active") {
            indicator.classList.add("active");
            stepEl.classList.add("active");
        } else if (status === "done") {
            indicator.classList.add("done");
            stepEl.classList.add("done");
        }
    }

    /**
     * İlerleme barını güncelle.
     */
    function setProgress(percent) {
        progressBarFill.style.width = percent + "%";
    }

    /**
     * İlerleme simülasyonu başlat.
     */
    function simulateProgress() {
        // Adım 1: Yükleniyor
        setProgressStep("upload", "active");
        setProgress(10);

        setTimeout(() => {
            setProgressStep("upload", "done");
            setProgressStep("transcribe", "active");
            setProgress(30);
        }, 800);

        setTimeout(() => {
            setProgress(50);
        }, 2000);

        setTimeout(() => {
            setProgressStep("transcribe", "done");
            setProgressStep("summarize", "active");
            setProgress(70);
        }, 4000);

        setTimeout(() => {
            setProgressStep("summarize", "done");
            setProgressStep("tasks", "active");
            setProgress(85);
        }, 5000);
    }

    /**
     * İlerleme göstergesini sıfırla.
     */
    function resetProgress() {
        Object.keys(progressSteps).forEach((key) => {
            setProgressStep(key, "idle");
        });
        setProgress(0);
    }


    // ─── Form Gönderimi ───────────────────────────────────────────────────────

    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Dosya kontrolü
        if (!fileInput.files || fileInput.files.length === 0) {
            showError("Lütfen bir ses dosyası seçin.");
            return;
        }

        // UI'ı işleniyor durumuna getir
        submitBtn.disabled = true;
        btnText.style.display = "none";
        btnLoader.style.display = "inline-flex";
        hideSection(errorSection);
        hideSection(resultsSection);
        showSection(progressSection);
        resetProgress();
        simulateProgress();

        // FormData oluştur ve gönder
        const formData = new FormData();
        let endpoint = "/upload";

        formData.append("audio_file", fileInput.files[0]);
        try {
            const response = await fetch(endpoint, {
                method: "POST",
                body: formData,
            });

            const data = await response.json();

            if (!response.ok || data.error) {
                throw new Error(data.error || "Sunucu hatası oluştu.");
            }

            // İlerlemeyi tamamla
            setProgressStep("tasks", "done");
            setProgress(100);

            // Kısa bir gecikme sonra sonuçları göster
            setTimeout(() => {
                hideSection(progressSection);
                hideSection(uploadSection);  // Yükleme formunu gizle
                displayResults(data);
            }, 600);

        } catch (err) {
            hideSection(progressSection);
            showError(err.message || "Beklenmeyen bir hata oluştu.");
        } finally {
            // Butonu sıfırla (loader'ı kapat ama disabled bırak — sonuçlar ekranda)
            btnText.style.display = "inline";
            btnLoader.style.display = "none";
        }
    });


    // ─── Sonuçları Göster ─────────────────────────────────────────────────────

    /**
     * Sunucudan gelen sonuçları arayüzde göster.
     */
    function displayResults(data) {
        // Dosya adını göster
        resultsFilename.textContent = data.filename || "";

        // ── Transkript ──
        transcriptContent.innerHTML = "";
        if (data.transcript) {
            // Birleşik metin yerine segmentleri daha güzel gösterebiliriz ama şimdilik düz metin veriyoruz
            const p = document.createElement("p");
            p.style.whiteSpace = "pre-line"; // Satır atlamalarını koru
            p.textContent = data.transcript;
            transcriptContent.appendChild(p);
        } else {
            transcriptContent.innerHTML = '<p class="no-tasks-message">Transkript oluşturulamadı.</p>';
        }

        // ── Özet ──
        summaryContent.innerHTML = "";
        if (data.summary) {
            const p = document.createElement("p");
            p.textContent = data.summary;
            summaryContent.appendChild(p);
        } else {
            summaryContent.innerHTML = '<p class="no-tasks-message">Özet oluşturulamadı.</p>';
        }

        // ── Görevler ──
        tasksContent.innerHTML = "";
        if (data.tasks && data.tasks.length > 0) {
            const ul = document.createElement("ul");
            ul.className = "task-list";

            data.tasks.forEach((task, index) => {
                const li = document.createElement("li");
                li.className = "task-item";
                li.style.animationDelay = (index * 0.05) + "s";

                li.innerHTML = `
                    <div class="task-bullet">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                            <polyline points="20 6 9 17 4 12"/>
                        </svg>
                    </div>
                    <span class="task-text">${escapeHtml(task)}</span>
                `;

                ul.appendChild(li);
            });

            tasksContent.appendChild(ul);

            // Görev sayısı badge'ini güncelle
            taskCountBadge.textContent = data.tasks.length;
            taskCountBadge.style.display = "inline";
        } else {
            tasksContent.innerHTML = '<p class="no-tasks-message">Metinde görev tespit edilemedi.</p>';
            taskCountBadge.style.display = "none";
        }

        // İlk tab'ı aktifle ve sonuçları göster
        activateTab("transcript");
        showSection(resultsSection);

        // Sonuçlara scroll
        resultsSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    /**
     * HTML injection'ı önlemek için özel karakterleri escape et.
     */
    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }


    // ─── Tab Yönetimi ─────────────────────────────────────────────────────────

    const tabButtons = document.querySelectorAll(".tab-btn");

    tabButtons.forEach((btn) => {
        btn.addEventListener("click", () => {
            const tabName = btn.getAttribute("data-tab");
            activateTab(tabName);
        });
    });

    /**
     * Belirtilen tab'ı aktifleştir.
     */
    function activateTab(tabName) {
        // Tüm butonları ve panelleri deaktive et
        tabButtons.forEach((b) => b.classList.remove("active"));
        document.querySelectorAll(".tab-pane").forEach((p) => p.classList.remove("active"));

        // Hedef tab'ı aktifle
        const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabName}"]`);
        const targetPane = document.getElementById(`pane-${tabName}`);

        if (targetBtn) targetBtn.classList.add("active");
        if (targetPane) targetPane.classList.add("active");
    }


    // ─── Hata Yönetimi ───────────────────────────────────────────────────────

    /**
     * Hata mesajını göster.
     */
    function showError(message) {
        errorMessage.textContent = message;
        showSection(errorSection);
    }

    errorDismissBtn.addEventListener("click", () => {
        hideSection(errorSection);
    });


    // ─── Yeni Dosya Yükle ─────────────────────────────────────────────────────

    newUploadBtn.addEventListener("click", () => {
        // Formu sıfırla
        fileInput.value = "";
        fileInfo.style.display = "none";
        submitBtn.disabled = true;

        // Sonuçları gizle, yükleme formunu geri getir
        hideSection(resultsSection);
        hideSection(errorSection);
        showSection(uploadSection);
        resetProgress();

        // Yükleme alanına scroll
        uploadSection.scrollIntoView({ behavior: "smooth", block: "center" });
    });
});
