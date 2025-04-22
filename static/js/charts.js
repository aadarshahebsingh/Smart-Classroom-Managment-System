/**
 * Chart creation and management for SCMS dashboards
 */

const ChartManager = {
    /**
     * Initialize charts on the page
     */
    init: function() {
        // Find all chart containers
        const chartContainers = document.querySelectorAll('[data-chart]');
        
        // Initialize each chart
        chartContainers.forEach(container => {
            const chartType = container.dataset.chart;
            const chartId = container.id;
            
            if (chartType && chartId) {
                this.createChart(chartId, chartType);
            }
        });
    },
    
    /**
     * Create a chart based on type and container ID
     */
    createChart: function(containerId, chartType) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        switch (chartType) {
            case 'attendance-overview':
                this.createAttendanceOverviewChart(container);
                break;
            case 'attendance-trend':
                this.createAttendanceTrendChart(container);
                break;
            case 'recognition-methods':
                this.createRecognitionMethodsChart(container);
                break;
            case 'class-attendance':
                this.createClassAttendanceChart(container);
                break;
            case 'student-attendance-history':
                this.createStudentAttendanceHistoryChart(container);
                break;
            default:
                console.warn(`Unknown chart type: ${chartType}`);
        }
    },
    
    /**
     * Create attendance overview chart (Admin dashboard)
     */
    createAttendanceOverviewChart: function(container) {
        // Get data from container data attributes
        const dates = JSON.parse(container.dataset.dates || '[]');
        const counts = JSON.parse(container.dataset.counts || '[]');
        const presentCounts = JSON.parse(container.dataset.presentCounts || '[]');
        
        // Create chart canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        
        // Create chart
        new Chart(canvas, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Total Records',
                        data: counts,
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        tension: 0.1
                    },
                    {
                        label: 'Present',
                        data: presentCounts,
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 2,
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Attendance Overview (Last 7 Days)'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    },
    
    /**
     * Create attendance trend chart (Admin reports)
     */
    createAttendanceTrendChart: function(container) {
        // Get data from container data attributes
        const labels = JSON.parse(container.dataset.labels || '[]');
        const present = JSON.parse(container.dataset.present || '[]');
        const absent = JSON.parse(container.dataset.absent || '[]');
        const late = JSON.parse(container.dataset.late || '[]');
        
        // Create chart canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        
        // Create chart
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Present',
                        data: present,
                        backgroundColor: 'rgba(75, 192, 192, 0.7)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Absent',
                        data: absent,
                        backgroundColor: 'rgba(255, 99, 132, 0.7)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Late',
                        data: late,
                        backgroundColor: 'rgba(255, 205, 86, 0.7)',
                        borderColor: 'rgba(255, 205, 86, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Count'
                        }
                    },
                    x: {
                        stacked: true
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Attendance Trend by Class'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    },
    
    /**
     * Create recognition methods chart (Admin reports)
     */
    createRecognitionMethodsChart: function(container) {
        // Get data from container data attributes
        const facialCount = parseInt(container.dataset.facialCount || '0');
        const manualCount = parseInt(container.dataset.manualCount || '0');
        
        // Create chart canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        
        // Create chart
        new Chart(canvas, {
            type: 'pie',
            data: {
                labels: ['Facial Recognition', 'Manual Entry'],
                datasets: [{
                    data: [facialCount, manualCount],
                    backgroundColor: [
                        'rgba(54, 162, 235, 0.7)',
                        'rgba(255, 159, 64, 0.7)'
                    ],
                    borderColor: [
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Attendance Recording Methods'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    },
                    legend: {
                        position: 'right'
                    }
                }
            }
        });
    },
    
    /**
     * Create class attendance chart (Teacher reports)
     */
    createClassAttendanceChart: function(container) {
        // Get data from container data attributes
        const students = JSON.parse(container.dataset.students || '[]');
        const presentDays = JSON.parse(container.dataset.presentDays || '[]');
        const totalDays = parseInt(container.dataset.totalDays || '0');
        
        // Calculate attendance percentages
        const percentages = presentDays.map(days => (days / totalDays * 100) || 0);
        
        // Create chart canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        
        // Create chart
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: students,
                datasets: [{
                    label: 'Attendance Rate (%)',
                    data: percentages,
                    backgroundColor: percentages.map(p => 
                        p >= 80 ? 'rgba(75, 192, 192, 0.7)' :  // Good (green)
                        p >= 60 ? 'rgba(255, 205, 86, 0.7)' :  // Average (yellow)
                        'rgba(255, 99, 132, 0.7)'              // Poor (red)
                    ),
                    borderColor: percentages.map(p => 
                        p >= 80 ? 'rgba(75, 192, 192, 1)' :
                        p >= 60 ? 'rgba(255, 205, 86, 1)' :
                        'rgba(255, 99, 132, 1)'
                    ),
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: 'Attendance Rate (%)'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Class Attendance Overview'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const index = context.dataIndex;
                                const present = presentDays[index];
                                return `Present: ${present}/${totalDays} days (${context.raw.toFixed(1)}%)`;
                            }
                        }
                    }
                }
            }
        });
    },
    
    /**
     * Create student attendance history chart (Student dashboard)
     */
    createStudentAttendanceHistoryChart: function(container) {
        // Get data from container data attributes
        const dates = JSON.parse(container.dataset.dates || '[]');
        const statuses = JSON.parse(container.dataset.statuses || '[]');
        
        // Create status arrays for the stacked chart
        const presentData = [];
        const absentData = [];
        const lateData = [];
        
        statuses.forEach(status => {
            if (status === 'present') {
                presentData.push(1);
                absentData.push(0);
                lateData.push(0);
            } else if (status === 'absent') {
                presentData.push(0);
                absentData.push(1);
                lateData.push(0);
            } else if (status === 'late') {
                presentData.push(0);
                absentData.push(0);
                lateData.push(1);
            } else {
                // No data
                presentData.push(0);
                absentData.push(0);
                lateData.push(0);
            }
        });
        
        // Create chart canvas
        const canvas = document.createElement('canvas');
        container.appendChild(canvas);
        
        // Create chart
        new Chart(canvas, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Present',
                        data: presentData,
                        backgroundColor: 'rgba(75, 192, 192, 0.7)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Absent',
                        data: absentData,
                        backgroundColor: 'rgba(255, 99, 132, 0.7)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Late',
                        data: lateData,
                        backgroundColor: 'rgba(255, 205, 86, 0.7)',
                        borderColor: 'rgba(255, 205, 86, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 1,
                        ticks: {
                            stepSize: 1,
                            callback: function(value) {
                                return value === 1 ? 'Yes' : 'No';
                            }
                        },
                        stacked: true
                    },
                    x: {
                        stacked: true
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Your Attendance History'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const datasetLabel = context.dataset.label || '';
                                return context.raw === 1 ? datasetLabel : '';
                            }
                        }
                    }
                }
            }
        });
    }
};

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ChartManager.init();
    
    // Reinitialize charts when tab changes (for Bootstrap tabs)
    const tabTriggers = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabTriggers.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            ChartManager.init();
        });
    });
});
