/**
 * Attendance management scripts
 */

const AttendanceManager = {
    /**
     * Initialize attendance functionality
     */
    init: function() {
        this.setupTabListeners();
        this.setupManualAttendance();
        this.setupFilterListeners();
        this.setupPrintFunctionality();
    },
    
    /**
     * Set up tab change listeners
     */
    setupTabListeners: function() {
        const tabTriggers = document.querySelectorAll('[data-bs-toggle="tab"]');
        tabTriggers.forEach(tab => {
            tab.addEventListener('shown.bs.tab', function(event) {
                // Update URL with active tab
                const tabId = event.target.getAttribute('href').substr(1);
                history.replaceState(null, null, `?tab=${tabId}`);
            });
        });
        
        // Set active tab from URL on page load
        const params = new URLSearchParams(window.location.search);
        const tabId = params.get('tab');
        if (tabId) {
            const tab = document.querySelector(`[href="#${tabId}"]`);
            if (tab) {
                const bootstrapTab = new bootstrap.Tab(tab);
                bootstrapTab.show();
            }
        }
    },
    
    /**
     * Set up manual attendance form handling
     */
    setupManualAttendance: function() {
        const manualForm = document.getElementById('manual-attendance-form');
        if (!manualForm) return;
        
        manualForm.addEventListener('submit', function(e) {
            // Form will be submitted normally, no need to prevent default
            // This is just for UI feedback
            const studentId = manualForm.querySelector('[name="student_id"]').value;
            const status = manualForm.querySelector('[name="status"]').value;
            
            // Update UI immediately for responsive feedback
            const statusElement = document.getElementById(`attendance-status-${studentId}`);
            if (statusElement) {
                statusElement.textContent = status.charAt(0).toUpperCase() + status.slice(1);
                
                // Update badge class
                statusElement.className = 'badge';
                if (status === 'present') {
                    statusElement.classList.add('badge-success');
                } else if (status === 'absent') {
                    statusElement.classList.add('badge-danger');
                } else if (status === 'late') {
                    statusElement.classList.add('badge-warning');
                }
            }
            
            // Update row color
            const rowElement = document.getElementById(`student-row-${studentId}`);
            if (rowElement) {
                // Remove existing status classes
                rowElement.classList.remove('table-success', 'table-danger', 'table-warning');
                
                // Add appropriate class
                if (status === 'present') {
                    rowElement.classList.add('table-success');
                } else if (status === 'absent') {
                    rowElement.classList.add('table-danger');
                } else if (status === 'late') {
                    rowElement.classList.add('table-warning');
                }
            }
        });
    },
    
    /**
     * Set up filters for reports
     */
    setupFilterListeners: function() {
        const reportForm = document.getElementById('reports-filter-form');
        if (!reportForm) return;
        
        // Auto-submit form when selects change
        const selectElements = reportForm.querySelectorAll('select');
        selectElements.forEach(select => {
            select.addEventListener('change', function() {
                reportForm.submit();
            });
        });
        
        // Set up date range pickers
        const dateRangeInputs = reportForm.querySelectorAll('input[type="date"]');
        dateRangeInputs.forEach(input => {
            // Use native date picker
            // Ensure today is the max date
            const today = new Date().toISOString().split('T')[0];
            input.setAttribute('max', today);
        });
    },
    
    /**
     * Set up report printing functionality
     */
    setupPrintFunctionality: function() {
        const printButtons = document.querySelectorAll('.btn-print');
        printButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                window.print();
            });
        });
        
        // Add print-specific styles
        this.addPrintStyles();
    },
    
    /**
     * Add print-specific styles
     */
    addPrintStyles: function() {
        const style = document.createElement('style');
        style.textContent = `
            @media print {
                .sidebar, .navbar, .no-print, form, button, .webcam-container {
                    display: none !important;
                }
                
                .main-content {
                    margin-left: 0 !important;
                    padding: 0 !important;
                }
                
                .card {
                    border: none !important;
                    box-shadow: none !important;
                }
                
                body {
                    background-color: white !important;
                }
                
                .table {
                    width: 100% !important;
                }
                
                @page {
                    size: portrait;
                    margin: 1cm;
                }
            }
        `;
        document.head.appendChild(style);
    },
    
    /**
     * Toggle attendance status manually
     */
    toggleStatus: function(studentId, currentStatus) {
        // Get status dropdown
        const statusSelect = document.querySelector('[name="status"]');
        if (!statusSelect) return;
        
        // Get student dropdown
        const studentSelect = document.querySelector('[name="student_id"]');
        if (!studentSelect) return;
        
        // Set values
        studentSelect.value = studentId;
        
        // Determine next status based on current status
        let nextStatus;
        if (!currentStatus || currentStatus === 'not_marked') {
            nextStatus = 'present';
        } else if (currentStatus === 'present') {
            nextStatus = 'late';
        } else if (currentStatus === 'late') {
            nextStatus = 'absent';
        } else {
            nextStatus = 'present';
        }
        
        statusSelect.value = nextStatus;
        
        // Submit the form
        const submitButton = document.querySelector('#manual-attendance-form [type="submit"]');
        if (submitButton) {
            submitButton.click();
        }
    },
    
    /**
     * Export attendance report to CSV
     */
    exportToCSV: function(tableId, filename = 'attendance_report.csv') {
        const table = document.getElementById(tableId);
        if (!table) return;
        
        let csv = [];
        const rows = table.querySelectorAll('tr');
        
        for (let i = 0; i < rows.length; i++) {
            const row = [], cols = rows[i].querySelectorAll('td, th');
            
            for (let j = 0; j < cols.length; j++) {
                // Clean the cell text
                let text = cols[j].innerText;
                
                // If cell contains badges, get only the badge text
                const badge = cols[j].querySelector('.badge');
                if (badge) {
                    text = badge.innerText;
                }
                
                // Replace commas, remove multiple spaces and newlines
                text = text.replace(/,/g, ';')
                          .replace(/\s\s+/g, ' ')
                          .trim();
                
                row.push('"' + text + '"');
            }
            
            csv.push(row.join(','));
        }
        
        // Download CSV file
        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    AttendanceManager.init();
});
