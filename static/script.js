document.addEventListener('DOMContentLoaded', () => {

    // ── Theme & Color ───────────────────────────────────────────────────────
    const html              = document.documentElement;
    const themeToggle       = document.getElementById('themeToggle');
    const colorPickerToggle = document.getElementById('colorPickerToggle');
    const colorDropdown     = document.getElementById('colorDropdown');

    // Restore saved preferences
    html.setAttribute('data-theme', localStorage.getItem('bioTheme') || 'dark');
    html.setAttribute('data-color', localStorage.getItem('bioColor') || 'pink');
    updateThemeIcon(html.getAttribute('data-theme'));

    themeToggle.addEventListener('click', () => {
        const next = html.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
        html.setAttribute('data-theme', next);
        localStorage.setItem('bioTheme', next);
        updateThemeIcon(next);
    });

    function updateThemeIcon(theme) {
        const icon = themeToggle.querySelector('i');
        if (theme === 'dark') {
            icon.className = 'fas fa-sun';
            themeToggle.title = 'Switch to Light Mode';
        } else {
            icon.className = 'fas fa-moon';
            themeToggle.title = 'Switch to Dark Mode';
        }
    }

    // Color picker open/close
    colorPickerToggle.addEventListener('click', (e) => {
        e.stopPropagation();
        colorDropdown.classList.toggle('show');
    });
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.color-picker-container')) {
            colorDropdown.classList.remove('show');
        }
    });

    document.querySelectorAll('.color-option').forEach(opt => {
        opt.addEventListener('click', () => {
            const color = opt.getAttribute('data-color');
            html.setAttribute('data-color', color);
            localStorage.setItem('bioColor', color);
            colorDropdown.classList.remove('show');
        });
    });


    // ── Cursor Flashlight / Glow Effect ────────────────────────────────────
    //
    // On every mousemove we update two CSS custom properties (--mouse-x,
    // --mouse-y) on <html>.  The .cursor-glow element's background is a
    // radial-gradient centred on those coordinates using var(--accent-cursor),
    // which automatically reflects whatever accent colour is active.
    //
    const glow = document.getElementById('cursorGlow');

    document.addEventListener('mousemove', (e) => {
        html.style.setProperty('--mouse-x', e.clientX + 'px');
        html.style.setProperty('--mouse-y', e.clientY + 'px');
    });

    // Hide the glow when the cursor leaves the window
    document.addEventListener('mouseleave', () => {
        html.style.setProperty('--mouse-x', '-9999px');
        html.style.setProperty('--mouse-y', '-9999px');
    });
    document.addEventListener('mouseenter', (e) => {
        html.style.setProperty('--mouse-x', e.clientX + 'px');
        html.style.setProperty('--mouse-y', e.clientY + 'px');
    });


    // ── Drag & Drop File Logic ──────────────────────────────────────────────
    const dropZone       = document.getElementById('dropZone');
    const fileInput      = document.getElementById('csvFile');
    const fileNameDisplay = document.getElementById('fileNameDisplay');
    const textarea       = document.getElementById('sequence');

    const preventDefaults = (e) => { e.preventDefault(); e.stopPropagation(); };
    ['dragenter','dragover','dragleave','drop'].forEach(ev => {
        dropZone.addEventListener(ev, preventDefaults);
        document.body.addEventListener(ev, preventDefaults);
    });
    ['dragenter','dragover'].forEach(ev => dropZone.addEventListener(ev, () => dropZone.classList.add('dragover')));
    ['dragleave','drop'].forEach(ev => dropZone.addEventListener(ev, () => dropZone.classList.remove('dragover')));

    dropZone.addEventListener('drop', (e) => handleFiles(e.dataTransfer.files));
    fileInput.addEventListener('change', function () { handleFiles(this.files); });

    function handleFiles(files) {
        if (!files.length) return;
        const file = files[0];
        if (!file.name.endsWith('.csv')) {
            alert('Please select a valid .csv file.');
            return;
        }
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;
        fileNameDisplay.innerHTML = `<i class="fas fa-file-csv"></i> Selected: ${file.name}`;
    }


    // ── Ensembl Database Fetch ──────────────────────────────────────────────
    const fetchBtn     = document.getElementById('fetchEnsemblBtn');
    const ensemblInput = document.getElementById('ensemblId');
    const statusEl     = document.getElementById('ensemblStatus');

    fetchBtn.addEventListener('click', async () => {
        const id = ensemblInput.value.trim();
        if (!id) {
            setStatus('Please enter an Ensembl ID (e.g. ENST00000380152).', 'error');
            return;
        }

        setStatus('Fetching from Ensembl REST API…', 'loading');
        fetchBtn.disabled = true;

        try {
            const res  = await fetch('/fetch_ensembl', {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ ensembl_id: id }),
            });

            if (!res.ok) {
                throw new Error(`Server error ${res.status}`);
            }

            const data = await res.json();

            if (data.success) {
                textarea.value = data.sequence;
                const mol  = data.molecule ? ` · ${data.molecule}` : '';
                const len  = data.sequence.length;
                setStatus(
                    `✓ Loaded "${data.desc}"${mol} — ${len.toLocaleString()} nt. Sequence pasted below.`,
                    'success'
                );
            } else {
                setStatus(`Error: ${data.error}`, 'error');
            }
        } catch (err) {
            setStatus(`Network error: ${err.message}`, 'error');
        } finally {
            fetchBtn.disabled = false;
        }
    });

    // Allow pressing Enter in the Ensembl input to trigger fetch
    ensemblInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') { e.preventDefault(); fetchBtn.click(); }
    });

    function setStatus(msg, type) {
        statusEl.textContent  = msg;
        statusEl.className    = `ensembl-status ${type}`;
    }

});
