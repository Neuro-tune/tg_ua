const GOOGLE_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbymLc_CQxyO9M9nZwuOjm_EHZa4aeiK8tzcLdCYp6Eh2tNTVPn95_UQ5_fYvKjpODr5/exec';

// Function to check busy slots (API)
async function getBusySlots(date) {
    try {
        console.log(`📡 Requesting slots for ${date}...`);
        const response = await fetch(`${GOOGLE_SCRIPT_URL}?date=${date}`);
        const data = await response.json();

        if (data.success) {
            console.log('🔒 Busy slots from table:', data.busy_slots);
            // Return array of times, e.g. ['14:00', '15:00']
            return data.busy_slots.map(slot => slot.time);
        }
        return [];
    } catch (e) {
        console.error('❌ Error getting slots:', e);
        return [];
    }
}

const tg = window.Telegram?.WebApp;

// Check if running in Telegram
const isTelegramWebApp = tg && tg.initData && tg.initData.length > 0;

// Initialize Web App
if (tg) {
    tg.ready();
    tg.expand();

    // Apply Telegram theme
    if (tg.themeParams) {
        document.body.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
        document.body.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
        document.body.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999');
        document.body.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#2481cc');
        document.body.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc');
        document.body.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f5f5f5');
    }

    // Add dark theme class
    if (tg.colorScheme === 'dark') {
        document.body.classList.add('dark-theme');
    }
}

console.log('🔍 Telegram WebApp detected:', isTelegramWebApp);

// ===== State Management =====
const state = {
    currentStep: 1,
    totalSteps: 3,
    formData: {
        name: '',
        phone: '',
        service: '',
        date: '',
        time: ''
    },
    selectedTimeSlot: null,
    busySlotsCache: [] // 🔥 Cache for busy slots to re-render without API calls
};

// ===== DOM Elements =====
const elements = {
    form: document.getElementById('bookingForm'),
    progressFill: document.getElementById('progressFill'),
    steps: document.querySelectorAll('.step'),
    formSteps: document.querySelectorAll('.form-step'),
    prevBtn: document.getElementById('prevBtn'),
    nextBtn: document.getElementById('nextBtn'),
    submitBtn: document.getElementById('submitBtn'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    summary: document.getElementById('summary'),

    // Inputs
    nameInput: document.getElementById('name'),
    phoneInput: document.getElementById('phone'),
    serviceSelect: document.getElementById('service'),
    dateInput: document.getElementById('date'),
    timeInput: document.getElementById('time'),
    timeSlotsContainer: document.getElementById('timeSlots'),

    // Service Info
    serviceInfo: document.getElementById('serviceInfo'),
    servicePrice: document.getElementById('servicePrice'),
    serviceDuration: document.getElementById('serviceDuration'),

    // Summary
    summaryName: document.getElementById('summaryName'),
    summaryPhone: document.getElementById('summaryPhone'),
    summaryService: document.getElementById('summaryService'),
    summaryDateTime: document.getElementById('summaryDateTime')
};

// ===== Utility Functions =====

function formatPhoneNumber(value) {
    const cleaned = value.replace(/\D/g, '');
    let formatted = '';
    if (cleaned.length === 0) return '';

    let digits = cleaned;
    // Ukrainian format logic
    if (cleaned.startsWith('380')) digits = cleaned;
    else if (cleaned.startsWith('0')) digits = '38' + cleaned;
    else digits = '380' + cleaned;

    digits = digits.substring(0, 12);

    formatted = '+' + digits.slice(0, 3);
    if (digits.length > 3) formatted += ' (' + digits.slice(3, 5);
    if (digits.length > 5) formatted += ') ' + digits.slice(5, 8);
    if (digits.length > 8) formatted += '-' + digits.slice(8, 10);
    if (digits.length > 10) formatted += '-' + digits.slice(10, 12);

    return formatted;
}

function isValidPhone(phone) {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length === 12 && cleaned.startsWith('380');
}

function isValidName(name) {
    return name.trim().length >= 2;
}

function formatDate(dateStr) {
    if (!dateStr) return 'Дата не обрана';
    const parts = dateStr.split('-');
    if (parts.length !== 3) return 'Невірний формат';
    const year = parseInt(parts[0], 10);
    const month = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    const date = new Date(year, month, day);
    if (isNaN(date.getTime())) return 'Невірна дата';

    const weekdays = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
    const months = ['січня', 'лютого', 'березня', 'квітня', 'травня', 'червня', 'липня', 'серпня', 'вересня', 'жовтня', 'листопада', 'грудня'];

    return `${weekdays[date.getDay()]}, ${day} ${months[date.getMonth()]} ${date.getFullYear()}`;
}

// Helper to add minutes to "HH:MM" string
function addMinutes(timeStr, minutesToAdd) {
    const [h, m] = timeStr.split(':').map(Number);
    const date = new Date();
    date.setHours(h, m + minutesToAdd);
    const newH = String(date.getHours()).padStart(2, '0');
    const newM = String(date.getMinutes()).padStart(2, '0');
    return `${newH}:${newM}`;
}

/**
 * Generate time slots
 */
function generateTimeSlots() {
    const slots = [];
    const startHour = 9;
    const endHour = 20;
    for (let hour = startHour; hour < endHour; hour++) {
        slots.push(`${hour.toString().padStart(2, '0')}:00`);
        slots.push(`${hour.toString().padStart(2, '0')}:30`);
    }
    return slots;
}

/**
 * 🔥 UPDATED SMART RENDER FUNCTION
 * Checks if the service duration fits into available slots
 */
function renderTimeSlots(busySlotsFromApi = []) {
    // 1. Update Cache
    state.busySlotsCache = busySlotsFromApi;

    const dateValue = elements.dateInput.value;
    if (!dateValue) {
        elements.timeSlotsContainer.innerHTML = '<p style="color: var(--tg-theme-hint-color); text-align: center; grid-column: 1/-1;">Спочатку оберіть дату</p>';
        return;
    }

    // 2. Get Service Duration
    const selectedOption = elements.serviceSelect.selectedOptions[0];
    let serviceDuration = 60; // Default to 60 mins
    if (selectedOption && selectedOption.dataset.duration) {
        serviceDuration = parseInt(selectedOption.dataset.duration);
    }

    const slots = generateTimeSlots();
    const now = new Date();
    const parts = dateValue.split('-');
    const selectedDate = new Date(parseInt(parts[0], 10), parseInt(parts[1], 10) - 1, parseInt(parts[2], 10));

    const today = new Date();
    today.setHours(0, 0, 0, 0);
    selectedDate.setHours(0, 0, 0, 0);
    const isToday = selectedDate.getTime() === today.getTime();

    console.log(`📅 Rendering. Duration: ${serviceDuration}m. Busy:`, busySlotsFromApi);

    elements.timeSlotsContainer.innerHTML = slots.map(slot => {
        let isDisabled = false;
        let tooltip = "";

        // Check 1: Is time past?
        if (isToday) {
            const [h, m] = slot.split(':').map(Number);
            const slotTime = new Date();
            slotTime.setHours(h, m, 0, 0);
            if (slotTime <= now) {
                isDisabled = true;
                tooltip = "Час минув";
            }
        }

        // Check 2: Is slot itself busy?
        if (!isDisabled && busySlotsFromApi.includes(slot)) {
            isDisabled = true;
            tooltip = "Вже зайнято";
        }

        // Check 3: 🔥 DOES IT FIT? (Smart Check)
        if (!isDisabled) {
            const blocksNeeded = Math.ceil(serviceDuration / 30);

            // Check current block + N future blocks
            for (let i = 0; i < blocksNeeded; i++) {
                const timeToCheck = addMinutes(slot, i * 30);

                // If future block is busy
                if (busySlotsFromApi.includes(timeToCheck)) {
                    isDisabled = true;
                    tooltip = "Недостатньо часу для послуги";
                    break;
                }

                // If future block is out of working hours (e.g. 20:30)
                // We check if 'timeToCheck' exists in our generated slots (except the start time)
                if (i > 0 && !slots.includes(timeToCheck)) {
                    isDisabled = true;
                    tooltip = "Скоро зачиняємось";
                    break;
                }
            }
        }

        const isSelected = state.selectedTimeSlot === slot;
        let classes = "time-slot";
        if (isDisabled) classes += " disabled";
        if (isSelected) classes += " selected";

        // Additional class for booked to style differently if needed
        if (tooltip === "Вже зайнято") classes += " booked";

        return `
            <div class="${classes}"
                 data-time="${slot}"
                 ${isDisabled ? 'data-disabled="true"' : ''}
                 ${isDisabled ? `title="${tooltip}"` : ''}>
                ${slot}
            </div>
        `;
    }).join('');

    // Add listeners
    document.querySelectorAll('.time-slot:not(.disabled)').forEach(slot => {
        slot.addEventListener('click', () => selectTimeSlot(slot));
    });
}

function selectTimeSlot(slotElement) {
    document.querySelectorAll('.time-slot').forEach(s => s.classList.remove('selected'));
    slotElement.classList.add('selected');
    state.selectedTimeSlot = slotElement.dataset.time;
    elements.timeInput.value = state.selectedTimeSlot;
    if (tg?.HapticFeedback) tg.HapticFeedback.selectionChanged();
    clearError('time');
    updateSummary();
}

// ===== Validation =====

function showError(fieldName, message) {
    const errorElement = document.getElementById(`${fieldName}Error`);
    const inputElement = document.getElementById(fieldName);
    if (errorElement) errorElement.textContent = message;
    if (inputElement) {
        inputElement.classList.add('error');
        inputElement.classList.remove('success');
    }
}

function clearError(fieldName) {
    const errorElement = document.getElementById(`${fieldName}Error`);
    const inputElement = document.getElementById(fieldName);
    if (errorElement) errorElement.textContent = '';
    if (inputElement) inputElement.classList.remove('error');
}

function showSuccess(fieldName) {
    const inputElement = document.getElementById(fieldName);
    if (inputElement) {
        inputElement.classList.remove('error');
        inputElement.classList.add('success');
    }
}

function validateCurrentStep() {
    let isValid = true;
    switch (state.currentStep) {
        case 1:
            if (!isValidName(elements.nameInput.value)) {
                showError('name', 'Введіть коректне ім\'я (мінімум 2 символи)');
                isValid = false;
            } else {
                clearError('name');
                showSuccess('name');
            }
            if (!isValidPhone(elements.phoneInput.value)) {
                showError('phone', 'Введіть коректний номер телефону');
                isValid = false;
            } else {
                clearError('phone');
                showSuccess('phone');
            }
            break;
        case 2:
            if (!elements.serviceSelect.value) {
                showError('service', 'Оберіть послугу');
                isValid = false;
            } else {
                clearError('service');
            }
            break;
        case 3:
            if (!elements.dateInput.value) {
                showError('date', 'Оберіть дату');
                isValid = false;
            } else {
                clearError('date');
            }
            if (!elements.timeInput.value) {
                showError('time', 'Оберіть час');
                isValid = false;
            } else {
                clearError('time');
            }
            break;
    }
    if (!isValid && tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
    return isValid;
}

// ===== Step Navigation =====

function updateProgress() {
    const progress = (state.currentStep / state.totalSteps) * 100;
    elements.progressFill.style.width = `${progress}%`;
    elements.steps.forEach((step, index) => {
        const stepNum = index + 1;
        step.classList.remove('active', 'completed');
        if (stepNum < state.currentStep) step.classList.add('completed');
        else if (stepNum === state.currentStep) step.classList.add('active');
    });
}

function goToStep(stepNumber) {
    elements.formSteps.forEach(step => step.classList.remove('active'));
    const newStep = document.querySelector(`.form-step[data-step="${stepNumber}"]`);
    if (newStep) newStep.classList.add('active');
    state.currentStep = stepNumber;
    updateProgress();
    updateButtons();
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (tg?.HapticFeedback) tg.HapticFeedback.selectionChanged();
}

function updateButtons() {
    elements.prevBtn.style.display = state.currentStep > 1 ? 'flex' : 'none';
    if (state.currentStep === state.totalSteps) {
        elements.nextBtn.style.display = 'none';
        elements.submitBtn.style.display = 'flex';
        elements.summary.style.display = 'block';
        updateSummary();
    } else {
        elements.nextBtn.style.display = 'flex';
        elements.submitBtn.style.display = 'none';
        elements.summary.style.display = 'none';
    }
}

function updateSummary() {
    const dateValue = elements.dateInput.value;
    const timeValue = elements.timeInput.value;
    elements.summaryName.textContent = elements.nameInput.value;
    elements.summaryPhone.textContent = elements.phoneInput.value;
    elements.summaryService.textContent = elements.serviceSelect.value;
    const formattedDate = formatDate(dateValue);
    const dateTimeString = timeValue ? `${formattedDate}, ${timeValue}` : formattedDate;
    elements.summaryDateTime.textContent = dateTimeString;
}

function nextStep() {
    if (validateCurrentStep()) {
        if (state.currentStep < state.totalSteps) goToStep(state.currentStep + 1);
    }
}

function prevStep() {
    if (state.currentStep > 1) goToStep(state.currentStep - 1);
}

// ===== Form Submission =====

async function submitForm(event) {
    event.preventDefault();
    if (!validateCurrentStep()) return;
    elements.loadingOverlay.classList.add('active');
    const dateValue = elements.dateInput.value;
    const timeValue = elements.timeInput.value;
    const formattedDateTime = `${formatDate(dateValue)}, ${timeValue}`;
    const formData = {
        name: elements.nameInput.value.trim(),
        phone: elements.phoneInput.value,
        service: elements.serviceSelect.value,
        datetime: formattedDateTime
    };
    console.log('📤 Submitting form data:', formData);
    await new Promise(resolve => setTimeout(resolve, 800));
    try {
        if (tg?.sendData) {
            tg.sendData(JSON.stringify(formData));
            if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
        } else {
            console.log('⚠️ Not running in Telegram WebApp');
            elements.loadingOverlay.classList.remove('active');
            showSuccessMessage(formData);
            return;
        }
    } catch (error) {
        console.error('❌ Error sending data:', error);
        if (tg?.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
        elements.loadingOverlay.classList.remove('active');
        if (tg?.showAlert) tg.showAlert('Виникла помилка при відправці даних');
        else alert('Виникла помилка при відправці даних');
    }
}

function showSuccessMessage(formData) {
    const modal = document.createElement('div');
    modal.className = 'success-modal';
    modal.innerHTML = `
        <div class="success-modal-content">
            <div class="success-icon">
                <span class="material-icons-round">check_circle</span>
            </div>
            <h2>Запис створено!</h2>
            <div class="success-details">
                <p><strong>Ім'я:</strong> ${formData.name}</p>
                <p><strong>Телефон:</strong> ${formData.phone}</p>
                <p><strong>Послуга:</strong> ${formData.service}</p>
                <p><strong>Дата/Час:</strong> ${formData.datetime}</p>
            </div>
            <p class="debug-note">⚠️ Debug mode: open in Telegram for real sending</p>
            <button class="btn btn-primary" onclick="this.closest('.success-modal').remove(); location.reload();">
                Закрити
            </button>
        </div>
    `;
    document.body.appendChild(modal);
}

// ===== Event Listeners =====

elements.phoneInput.addEventListener('input', (e) => {
    e.target.value = formatPhoneNumber(e.target.value);
});

// 🔥 UPDATED SERVICE LISTENER
// Now it re-renders slots if date is selected (to apply new duration check)
elements.serviceSelect.addEventListener('change', (e) => {
    const selectedOption = e.target.selectedOptions[0];
    const price = selectedOption.dataset.price;
    const duration = selectedOption.dataset.duration;

    if (price && duration) {
        elements.servicePrice.textContent = `${parseInt(price).toLocaleString('uk-UA')} ₴`;
        elements.serviceDuration.textContent = `${duration} хв`;
        elements.serviceInfo.style.display = 'block';
    } else {
        elements.serviceInfo.style.display = 'none';
    }
    clearError('service');

    // If date is already selected, re-check slots with new duration
    if (elements.dateInput.value) {
        renderTimeSlots(state.busySlotsCache);
    }
});

function setupDateInput() {
    const today = new Date();
    const maxDate = new Date();
    maxDate.setMonth(maxDate.getMonth() + 2);
    const formatForInput = (date) => {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    };
    elements.dateInput.min = formatForInput(today);
    elements.dateInput.max = formatForInput(maxDate);
}

elements.dateInput.addEventListener('change', async (e) => {
    const date = e.target.value;
    console.log('📅 Date changed:', date);
    clearError('date');
    state.selectedTimeSlot = null;
    elements.timeInput.value = '';

    if (date) {
        elements.timeSlotsContainer.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 20px; color: var(--tg-theme-hint-color);">
                ⏳ Перевірка розкладу...
            </div>
        `;
        const realBusySlots = await getBusySlots(date);
        renderTimeSlots(realBusySlots);
    } else {
        renderTimeSlots([]);
    }
    updateSummary();
});

elements.nameInput.addEventListener('input', () => clearError('name'));
elements.phoneInput.addEventListener('input', () => clearError('phone'));
elements.nextBtn.addEventListener('click', nextStep);
elements.prevBtn.addEventListener('click', prevStep);
elements.form.addEventListener('submit', submitForm);

// ===== Initialization =====

function init() {
    setupDateInput();
    updateProgress();
    updateButtons();
    renderTimeSlots();
    if (!isTelegramWebApp) console.log('⚠️ Running in debug mode');
    console.log('🚀 Booking form initialized');
}

document.addEventListener('DOMContentLoaded', init);