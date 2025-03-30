/**
 * Main JavaScript functionality for Concession Stand Inventory Management System
 */

// Define global namespace to avoid conflicts
const ConStand = {
    // Configuration options
    config: {
        apiBasePath: '/api',
        refreshInterval: 60000, // 1 minute default for data refresh
    },
    
    // API utilities
    api: {
        // Generic GET request
        get: function(endpoint, params = {}) {
            let url = new URL(`${ConStand.config.apiBasePath}/${endpoint}`, window.location.origin);
            
            // Add query parameters
            Object.keys(params).forEach(key => {
                if (params[key] !== undefined && params[key] !== null) {
                    url.searchParams.append(key, params[key]);
                }
            });
            
            return fetch(url.toString())
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`API Error: ${response.status}`);
                    }
                    return response.json();
                })
                .catch(error => {
                    console.error('API request failed:', error);
                    ConStand.ui.showError(`Failed to fetch data: ${error.message}`);
                    return [];
                });
        },
        
        // Generic POST request
        post: function(endpoint, data) {
            return fetch(`${ConStand.config.apiBasePath}/${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.detail || `API Error: ${response.status}`);
                    });
                }
                return response.json();
            })
            .catch(error => {
                console.error('API request failed:', error);
                ConStand.ui.showError(`Failed to submit data: ${error.message}`);
                throw error;
            });
        },
        
        // Generic PUT request
        put: function(endpoint, data) {
            return fetch(`${ConStand.config.apiBasePath}/${endpoint}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => {
                        throw new Error(err.detail || `API Error: ${response.status}`);
                    });
                }
                return response.json();
            })
            .catch(error => {
                console.error('API request failed:', error);
                ConStand.ui.showError(`Failed to update data: ${error.message}`);
                throw error;
            });
        },
        
        // Generic DELETE request
        delete: function(endpoint) {
            return fetch(`${ConStand.config.apiBasePath}/${endpoint}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`API Error: ${response.status}`);
                }
                return true;
            })
            .catch(error => {
                console.error('API request failed:', error);
                ConStand.ui.showError(`Failed to delete data: ${error.message}`);
                throw error;
            });
        }
    },
    
    // UI utilities
    ui: {
        // Show error notification
        showError: function(message) {
            const alertHtml = `
                <div class="alert alert-danger alert-dismissible fade show" role="alert">
                    <strong>Error!</strong> ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            
            // Prepend to the main container
            const container = document.querySelector('.container');
            if (container) {
                const alertElement = document.createElement('div');
                alertElement.innerHTML = alertHtml;
                container.prepend(alertElement.firstChild);
                
                // Auto-dismiss after 5 seconds
                setTimeout(() => {
                    const alert = document.querySelector('.alert');
                    if (alert) {
                        alert.remove();
                    }
                }, 5000);
            }
        },
        
        // Show success notification
        showSuccess: function(message) {
            const alertHtml = `
                <div class="alert alert-success alert-dismissible fade show" role="alert">
                    <strong>Success!</strong> ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
                </div>
            `;
            
            // Prepend to the main container
            const container = document.querySelector('.container');
            if (container) {
                const alertElement = document.createElement('div');
                alertElement.innerHTML = alertHtml;
                container.prepend(alertElement.firstChild);
                
                // Auto-dismiss after 5 seconds
                setTimeout(() => {
                    const alert = document.querySelector('.alert');
                    if (alert) {
                        alert.remove();
                    }
                }, 5000);
            }
        },
        
        // Format currency
        formatCurrency: function(amount) {
            return '$' + parseFloat(amount).toFixed(2);
        },
        
        // Format date
        formatDate: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleDateString();
        },
        
        // Format time
        formatTime: function(dateString) {
            const date = new Date(dateString);
            return date.toLocaleTimeString();
        }
    },
    
    // Functions for TV display
    display: {
        // Initialize a display for a specific stand
        initDisplay: function(standId) {
            // Fetch menu data for this stand
            ConStand.api.get(`display/menu/${standId}`)
                .then(data => {
                    ConStand.display.renderMenu(data);
                    
                    // Set up auto-refresh
                    setInterval(() => {
                        ConStand.api.get(`display/menu/${standId}`)
                            .then(newData => {
                                ConStand.display.renderMenu(newData);
                            });
                    }, ConStand.config.refreshInterval);
                });
        },
        
        // Render menu data on the display
        renderMenu: function(menuData) {
            // Implementation will be specific to the TV display template
            console.log('Menu data updated:', menuData);
        }
    }
};

// Run when the document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Concession Stand Inventory Management initialized');
    
    // Handle active nav links
    const currentPath = window.location.pathname;
    document.querySelectorAll('.navbar-nav .nav-link').forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
});