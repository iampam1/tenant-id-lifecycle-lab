// Main JavaScript file for Tenant Lifecycle Lab
console.log("Main JS loaded - v2.");

const API_BASE_URL = '/api/v1'; // Defined for convenience

/**
 * Checks authentication status and updates the navigation bar.
 * Redirects to login if no token is found and redirectIfNoToken is true.
 * @param {boolean} redirectIfNoToken - Whether to redirect to /ui/login if no token.
 */
function checkAuthStatusAndUpdateNavbar(redirectIfNoToken = true) {
    const token = localStorage.getItem('accessToken');
    const authLink = document.getElementById('authLink'); // Assumes an element with id="authLink" exists

    if (authLink) {
        if (token) {
            authLink.textContent = 'Logout';
            authLink.href = '#logout'; // Prevent default navigation
            authLink.onclick = function(e) {
                e.preventDefault();
                localStorage.removeItem('accessToken');
                localStorage.removeItem('tokenType');
                window.location.href = '/ui/login';
            };
        } else {
            authLink.textContent = 'Login';
            authLink.href = '/ui/login';
            authLink.onclick = null; // Remove any previous logout handler
            if (redirectIfNoToken) {
                // Only redirect if we are not already on a public page like login/register
                if (!window.location.pathname.endsWith('/ui/login') && !window.location.pathname.endsWith('/ui/register')) {
                    window.location.href = '/ui/login';
                }
            }
        }
    }
}

/**
 * A helper function to make authenticated API calls using fetch.
 * @param {string} url - The API endpoint URL (e.g., '/users/me').
 * @param {object} options - Fetch options (method, body, headers, etc.).
 * @returns {Promise<Response>} The fetch Response object.
 */
async function fetchWithAuth(url, options = {}) {
    const token = localStorage.getItem('accessToken');
    const headers = {
        ...options.headers, // Spread existing headers from options
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Ensure Content-Type is set for relevant methods if body is JSON
    if (options.body && typeof options.body === 'object' && !headers['Content-Type']) {
        if (!(options.body instanceof URLSearchParams) && !(options.body instanceof FormData)) {
             headers['Content-Type'] = 'application/json';
             options.body = JSON.stringify(options.body);
        }
    }

    const finalOptions = { ...options, headers };

    const response = await fetch(url, finalOptions);

    if (response.status === 401) {
        // Unauthorized: Token might be expired or invalid.
        // Clear token and redirect to login.
        console.warn('Unauthorized API request. Token might be invalid or expired.');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('tokenType');
        if (!window.location.pathname.endsWith('/ui/login')) { // Avoid redirect loop
             window.location.href = '/ui/login?session_expired=true';
        }
    }
    return response;
}

// Generic error display helper
function displayError(elementId, message) {
    const errorDiv = document.getElementById(elementId);
    if (errorDiv) {
        errorDiv.textContent = message || 'An error occurred.';
        errorDiv.style.display = 'block';
    }
}

function displaySuccess(elementId, message) {
    const successDiv = document.getElementById(elementId);
    if (successDiv) {
        successDiv.textContent = message || 'Success!';
        successDiv.style.display = 'block';
    }
}

function clearMessages(errorElementId, successElementId) {
    const errorDiv = document.getElementById(errorElementId);
    const successDiv = document.getElementById(successElementId);
    if (errorDiv) { errorDiv.style.display = 'none'; errorDiv.textContent = '';}
    if (successDiv) { successDiv.style.display = 'none'; successDiv.textContent = '';}
}


// Call on DOMContentLoaded for all pages that include main.js
// For pages requiring auth, they will handle their own redirect if this doesn't.
// The `redirectIfNoToken` parameter in `checkAuthStatusAndUpdateNavbar` determines behavior.
// For login/register pages, we would call checkAuthStatusAndUpdateNavbar(false).
// For protected pages, we call checkAuthStatusAndUpdateNavbar(true) or just checkAuthStatusAndUpdateNavbar().
// This initial call updates the navbar for all pages. Specific page scripts can then decide to redirect.
document.addEventListener('DOMContentLoaded', function() {
    // Default behavior: update navbar, don't force redirect from main.js
    // Page-specific scripts will handle mandatory redirection.
    checkAuthStatusAndUpdateNavbar(false);
});
