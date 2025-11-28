document.addEventListener('DOMContentLoaded', () => {
    // ---- Keep your existing sidebar code here ----
    const openBtn = document.getElementById('menu-open-btn');
    const closeBtn = document.getElementById('menu-close-btn');
    const sidebar = document.getElementById('sidebar-menu');
    const overlay = document.getElementById('overlay');

    if (openBtn && closeBtn && sidebar && overlay) {
        function openSidebar() {
            sidebar.classList.remove('translate-x-full');
            overlay.classList.remove('hidden');
            document.body.classList.add('overflow-hidden');
        }

        function closeSidebar() {
            sidebar.classList.add('translate-x-full');
            overlay.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }

        openBtn.addEventListener('click', openSidebar);
        closeBtn.addEventListener('click', closeSidebar);
        overlay.addEventListener('click', closeSidebar);
    }

    // --- START: New Password Validation and Toggle Logic ---
    const passwordInput = document.getElementById('password');
    const togglePasswordBtn = document.getElementById('toggle-password');
    const eyeIcon = document.getElementById('eye-icon');
    const eyeOffIcon = document.getElementById('eye-off-icon');

    // Password strength checklist elements
    const lengthCheck = document.getElementById('length');
    const lowercaseCheck = document.getElementById('lowercase');
    const uppercaseCheck = document.getElementById('uppercase');
    const numberCheck = document.getElementById('number');
    const specialCheck = document.getElementById('special');

    // Only run this script if we are on the register or account page
    if (passwordInput && lengthCheck) {
        // --- Password Visibility Toggle (if button exists) ---
        if (togglePasswordBtn) {
            togglePasswordBtn.addEventListener('click', () => {
                if (passwordInput.type === 'password') {
                    passwordInput.type = 'text';
                    if (eyeIcon) eyeIcon.classList.add('hidden');
                    if (eyeOffIcon) eyeOffIcon.classList.remove('hidden');
                } else {
                    passwordInput.type = 'password';
                    if (eyeIcon) eyeIcon.classList.remove('hidden');
                    if (eyeOffIcon) eyeOffIcon.classList.add('hidden');
                }
            });
        }

        // --- Real-time Password Strength Validation ---
        passwordInput.addEventListener('input', () => {
            const value = passwordInput.value;
            
            const updateCheck = (element, isValid) => {
                if (element) { // Check if the element exists
                    if (isValid) {
                        element.classList.add('text-green-500');
                        element.classList.remove('text-slate-500');
                    } else {
                        element.classList.remove('text-green-500');
                        element.classList.add('text-slate-500');
                    }
                }
            };
            
            updateCheck(lengthCheck, value.length >= 8);
            updateCheck(lowercaseCheck, /[a-z]/.test(value));
            updateCheck(uppercaseCheck, /[A-Z]/.test(value));
            updateCheck(numberCheck, /\d/.test(value));
            updateCheck(specialCheck, /[\W_]/.test(value));
        });
    }

    // --- START: New AJAX Contact Form Submission Logic ---
    const contactForm = document.getElementById('contact-form');
    const submitButton = document.getElementById('submit-button');
    const formStatus = document.getElementById('form-status');

    if (contactForm) {
        contactForm.addEventListener('submit', function(event) {
            event.preventDefault(); 

            const formData = new FormData(this);

            submitButton.disabled = true;
            submitButton.textContent = 'Sending...';
            formStatus.textContent = '';

            fetch(this.action, {
                method: this.method,
                body: formData,
                headers: {
                    'Accept': 'application/json'
                }
            }).then(response => {
                if (response.ok) {
                    formStatus.innerHTML = '<p class="text-green-600 font-bold">Thank you for your message! We will get back to you soon.</p>';
                    contactForm.reset();
                    submitButton.style.display = 'none'; 
                } else {
                    response.json().then(data => {
                        if (Object.hasOwn(data, 'errors')) {
                            formStatus.innerHTML = `<p class="text-red-600">${data["errors"].map(error => error["message"]).join(", ")}</p>`;
                        } else {
                            formStatus.innerHTML = '<p class="text-red-600">Oops! There was a problem submitting your form.</p>';
                        }
                        submitButton.disabled = false;
                        submitButton.textContent = 'Send Message';
                    });
                }
            }).catch(error => {
                formStatus.innerHTML = '<p class="text-red-600">Oops! There was a network error. Please try again.</p>';
                submitButton.disabled = false;
                submitButton.textContent = 'Send Message';
            });
        });
    }

    // ===== START: ADDED TERMS & CONDITIONS MODAL LOGIC =====
    const registerForm = document.getElementById('register-form');
    const showTermsBtn = document.getElementById('show-terms-modal-btn');
    const termsModal = document.getElementById('terms-modal');
    const cancelTermsBtn = document.getElementById('cancel-terms-btn');
    const confirmTermsBtn = document.getElementById('confirm-terms-btn');
    const termsCheckbox = document.getElementById('terms-checkbox');
    
    // Only run this script if all the registration modal elements exist on the page
    if (registerForm && showTermsBtn && termsModal) {
        
        // Show the modal when the main "Create Account" button is clicked
        showTermsBtn.addEventListener('click', () => {
            termsModal.classList.remove('hidden');
        });

        // Hide the modal
        function closeModal() {
            termsModal.classList.add('hidden');
        }

        cancelTermsBtn.addEventListener('click', closeModal);
        
        // Enable/disable the confirm button based on the checkbox state
        termsCheckbox.addEventListener('change', () => {
            if (termsCheckbox.checked) {
                confirmTermsBtn.disabled = false;
            } else {
                confirmTermsBtn.disabled = true;
            }
        });

        // When the user confirms, programmatically submit the actual registration form
        confirmTermsBtn.addEventListener('click', () => {
            if (termsCheckbox.checked) {
                registerForm.submit();
            }
        });
    }
    // ===== END: ADDED TERMS & CONDITIONS MODAL LOGIC =====

});