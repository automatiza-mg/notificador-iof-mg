// Funções JavaScript para gerenciar formulários e interações

let termsList = [];
let emailsList = [];
const MAX_TERMS = 5;
const MAX_EMAILS = 5;

// ========== RENDERIZAÇÃO E GERENCIAMENTO ==========

function renderTerms() {
    const container = document.getElementById('termsContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    termsList.forEach((term, index) => {
        const termDiv = document.createElement('div');
        termDiv.className = 'flex items-center justify-between px-4 py-2 bg-white border border-gray-300 rounded-full mb-2 shadow-sm';
        
        // Input escondido real (usado só pro envio final pelo submit handler pra gente preencher os exacts globais depois)
        // Por ora deixamos um data-term
        
        termDiv.innerHTML = `
            <span class="text-sm text-gray-800 truncate flex-1 mr-4">${escapeHtml(term)}</span>
            <div class="flex items-center gap-1.5 shrink-0">
                <button type="button" onclick="editSearchTerm(${index})" class="w-8 h-8 flex items-center justify-center bg-gray-200 hover:bg-gray-300 rounded-full transition text-gray-600">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                </button>
                <button type="button" onclick="removeSearchTerm(${index})" class="w-8 h-8 flex items-center justify-center bg-gray-200 hover:bg-gray-300 rounded-full transition text-gray-600">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;
        
        container.appendChild(termDiv);
    });
    
    updateTermButtons();
}

function renderEmails() {
    const container = document.getElementById('emailsContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    emailsList.forEach((email, index) => {
        const emailDiv = document.createElement('div');
        emailDiv.className = 'flex items-center justify-between px-4 py-2 bg-white border border-gray-300 rounded-full mb-2 shadow-sm';
        
        emailDiv.innerHTML = `
            <span class="text-sm text-gray-800 truncate flex-1 mr-4">${escapeHtml(email)}</span>
            <input type="hidden" name="mail_to" value="${escapeHtml(email)}">
            <div class="flex items-center gap-1.5 shrink-0">
                <button type="button" onclick="editEmail(${index})" class="w-8 h-8 flex items-center justify-center bg-gray-200 hover:bg-gray-300 rounded-full transition text-gray-600">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                    </svg>
                </button>
                <button type="button" onclick="removeEmailField(${index})" class="w-8 h-8 flex items-center justify-center bg-gray-200 hover:bg-gray-300 rounded-full transition text-gray-600">
                    <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="3 6 5 6 21 6"></polyline>
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                </button>
            </div>
        `;
        
        container.appendChild(emailDiv);
    });
    
    updateEmailButtons();
}

// ========== ACOES DE TERMOS ==========

function addSearchTermAction() {
    const input = document.getElementById('newTerm');
    if (!input) return;
    
    const termValue = input.value.trim();
    if (!termValue) return;
    
    if (termsList.length >= MAX_TERMS) {
        alert(`Você pode adicionar no máximo ${MAX_TERMS} termos.`);
        return;
    }
    
    if (termsList.includes(termValue)) {
        alert('Este termo já foi adicionado.');
        return;
    }
    
    termsList.push(termValue);
    input.value = '';
    renderTerms();
}

function removeSearchTerm(index) {
    termsList.splice(index, 1);
    renderTerms();
}

function editSearchTerm(index) {
    const input = document.getElementById('newTerm');
    if (!input) return;
    
    // Put term back in input
    input.value = termsList[index];
    input.focus();
    
    // Remove from list to allow re-adding
    removeSearchTerm(index);
}

function updateTermButtons() {
    const addBtn = document.getElementById('addTermBtn');
    const input = document.getElementById('newTerm');
    
    if (addBtn) addBtn.disabled = termsList.length >= MAX_TERMS;
    if (input) input.disabled = termsList.length >= MAX_TERMS;
}

// ========== ACOES DE EMAILS ==========

function addEmailAction() {
    const input = document.getElementById('newEmail');
    if (!input) return;
    
    const emailValue = input.value.trim();
    if (!emailValue) return;
    
    if (emailsList.length >= MAX_EMAILS) {
        alert(`Você pode adicionar no máximo ${MAX_EMAILS} emails.`);
        return;
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailValue)) {
        alert('Por favor, insira um email válido.');
        return;
    }
    
    if (emailsList.includes(emailValue)) {
        alert('Este email já foi adicionado.');
        return;
    }
    
    emailsList.push(emailValue);
    input.value = '';
    renderEmails();
}

function removeEmailField(index) {
    emailsList.splice(index, 1);
    renderEmails();
}

function editEmail(index) {
    const input = document.getElementById('newEmail');
    if (!input) return;
    
    input.value = emailsList[index];
    input.focus();
    
    removeEmailField(index);
}

function updateEmailButtons() {
    const addBtn = document.getElementById('addEmailBtn');
    const input = document.getElementById('newEmail');
    
    if (addBtn) addBtn.disabled = emailsList.length >= MAX_EMAILS;
    if (input) input.disabled = emailsList.length >= MAX_EMAILS;
}

// ========== INITIALIZATION AND LISTENERS ==========

document.addEventListener('DOMContentLoaded', function() {
    
    // Setup terms input
    const addTermBtn = document.getElementById('addTermBtn');
    const newTermInput = document.getElementById('newTerm');
    
    if (addTermBtn && newTermInput) {
        addTermBtn.addEventListener('click', addSearchTermAction);
        newTermInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addSearchTermAction();
            }
        });
    }

    // Setup emails input
    const addEmailBtn = document.getElementById('addEmailBtn');
    const newEmailInput = document.getElementById('newEmail');
    
    if (addEmailBtn && newEmailInput) {
        addEmailBtn.addEventListener('click', addEmailAction);
        newEmailInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                e.preventDefault();
                addEmailAction();
            }
        });
    }
    
    // Prevent form submit on global enter if not inside a specific flow
    const form = document.getElementById('configForm');
    if (form) {
        form.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
                e.preventDefault();
            }
        });
        
        // Final submit interception to build hidden fields
        form.addEventListener('submit', function(e) {
            
            if (termsList.length === 0) {
                alert('É necessário adicionar pelo menos um termo de busca.');
                e.preventDefault();
                return false;
            }

            if (emailsList.length === 0) {
                alert('É necessário adicionar pelo menos um email.');
                e.preventDefault();
                return false;
            }
            
            // The type of search (exact or partial) is global now in our UI
            // 0 means global Exact, 1 means global Partial (or whatever logic radio uses)
            const isGlobalExact = document.getElementById('radioExata').checked;
            
            // Clean any previously generated hidden inputs just in case
            document.querySelectorAll('.generated-hidden-term').forEach(el => el.remove());
            
            // Create hidden fields for each term to match backend expectation
            termsList.forEach(term => {
                const termInput = document.createElement('input');
                termInput.type = 'hidden';
                termInput.name = 'term';
                termInput.value = term;
                termInput.className = 'generated-hidden-term';
                form.appendChild(termInput);
                
                const exactInput = document.createElement('input');
                exactInput.type = 'hidden';
                exactInput.name = 'term_exact';
                exactInput.value = isGlobalExact ? 'on' : 'off';
                exactInput.className = 'generated-hidden-term';
                form.appendChild(exactInput);
            });
            
            // UI Feedback para Submit
            const submitBtn = document.getElementById('submitBtn');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = `
                    <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline-block" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processando...
                `;
                submitBtn.classList.add('opacity-75', 'cursor-not-allowed');
            }
            
            return true;
        });
    }
});

// ========== UTILITÁRIOS ==========

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Helper to be called from inline script in create/edit html
function initializeForm(initialTermsData, initialEmailsData, isAllExact) {
    // initialTermsData: [{term: "foo", exact: true}]
    if (initialTermsData && initialTermsData.length > 0) {
        termsList = initialTermsData.map(t => t.term);
        // We set the radio based on the first term (since it's a global setting now)
        if (initialTermsData.length > 0) {
             const exactRadio = document.getElementById('radioExata');
             const ampliadaRadio = document.getElementById('radioAmpliada');
             
             // Try to use parameter if provided, otherwise fallback to first term
             const exactStatus = isAllExact !== undefined ? isAllExact : initialTermsData[0].exact;
             
             if(exactRadio && ampliadaRadio) {
                 if(exactStatus) {
                     exactRadio.checked = true;
                 } else {
                     ampliadaRadio.checked = true;
                 }
             }
        }
    }
    
    if (initialEmailsData && initialEmailsData.length > 0) {
        emailsList = initialEmailsData;
    }
    
    renderTerms();
    renderEmails();
}
