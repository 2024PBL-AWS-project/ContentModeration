let moderationChart;
let alertCount = 0;
let totalFrames = 0;

function initializeChart() {
    const ctx = document.getElementById('moderationChart').getContext('2d');
    moderationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Non-Explicit Nudity',
                borderColor: 'rgb(255, 99, 132)',
                data: [],
                fill: false
            }, {
                label: 'Explicit Content',
                borderColor: 'rgb(54, 162, 235)',
                data: [],
                fill: false
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    title: {
                        display: true,
                        text: 'Confidence Level (%)'
                    }
                }
            },
            animation: {
                duration: 0
            }
        }
    });
}

function updateDashboard(moderationData) {
    if (!moderationChart) {
        initializeChart();
    }

    totalFrames++;
    document.getElementById('totalFrames').textContent = `Total Frames: ${totalFrames}`;

    const timestamp = new Date().toLocaleTimeString();
    
    // Find the highest confidence values for each category
    let nonExplicitConfidence = 0;
    let explicitConfidence = 0;

    moderationData.forEach(label => {
        if (label.Name.includes('Non-Explicit')) {
            nonExplicitConfidence = Math.max(nonExplicitConfidence, label.Confidence);
        } else if (label.Name.includes('Explicit')) {
            explicitConfidence = Math.max(explicitConfidence, label.Confidence);
        }
    });

    // Update alert count if confidence thresholds are met
    if (explicitConfidence > 80 || nonExplicitConfidence > 90) {
        alertCount++;
        document.getElementById('alertCount').textContent = `Alerts: ${alertCount}`;
    }

    // Update chart data
    moderationChart.data.labels.push(timestamp);
    moderationChart.data.datasets[0].data.push(nonExplicitConfidence);
    moderationChart.data.datasets[1].data.push(explicitConfidence);

    // Keep only last 20 data points
    if (moderationChart.data.labels.length > 20) {
        moderationChart.data.labels.shift();
        moderationChart.data.datasets.forEach(dataset => dataset.data.shift());
    }

    moderationChart.update();
}

// Listen for moderation results
setInterval(() => {
    fetch('/get_results')
        .then(response => response.json())
        .then(data => {
            if (data && data.length > 0) {
                const latestResult = data[0];
                console.log('>>>>Latest result:', latestResult);
                if (latestResult.ModerationLabels) {
                    updateDashboard(latestResult.ModerationLabels);
                }
            }
        })
        .catch(error => console.error('Error updating dashboard:', error));
}, 1000);

// Initialize chart when page loads
document.addEventListener('DOMContentLoaded', initializeChart);