let frameCount = 0;

function getConfidenceClass(confidence) {
    if (confidence > 80) return 'confidence-high';
    if (confidence > 50) return 'confidence-medium';
    return 'confidence-low';
}

function formatTimestamp(isoString) {
    try {
        return new Date(isoString).toLocaleTimeString();
    } catch (e) {
        return 'Invalid timestamp';
    }
}

function updateResults() {
    fetch('/get_results')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(items => {
            console.log('Received items:', items);
            if (!Array.isArray(items) || items.length === 0) {
                throw new Error('No data available');
            }

            const resultsDiv = document.getElementById('moderationResults');
            const alertDiv = document.getElementById('alert');
            const latestResult = items[0];  // Most recent result
            
            // Update frame count
            frameCount++;
            document.querySelectorAll('#frameCount').forEach(el => {
                el.textContent = frameCount;
            });

            // Update last processed timestamp
            document.querySelectorAll('#lastProcessed').forEach(el => {
                el.textContent = formatTimestamp(latestResult.timestamp);
            });

            // Check if there are moderation labels
            if (latestResult.labels && latestResult.labels.length > 0) {
                // Show alert for concerning content
                alertDiv.style.display = 'block';
                alertDiv.classList.add('alert-active');
                
                const labelsHtml = latestResult.labels
                    .map(label => `
                        <div class="label-item ${getConfidenceClass(label.Confidence)}">
                            <strong>${label.Name}</strong>
                            <div class="confidence">
                                Confidence: ${label.Confidence.toFixed(2)}%
                                <div class="progress">
                                    <div class="progress-bar" 
                                         style="width: ${label.Confidence}%" 
                                         aria-valuenow="${label.Confidence}" 
                                         aria-valuemin="0" 
                                         aria-valuemax="100">
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('');

                resultsDiv.innerHTML = `
                    <div class="timestamp">Last updated: ${formatTimestamp(latestResult.timestamp)}</div>
                    ${labelsHtml}
                `;
            } else {
                // Hide alert for clean content
                alertDiv.style.display = 'none';
                alertDiv.classList.remove('alert-active');
                resultsDiv.innerHTML = '<div class="label-item safe">No content concerns detected</div>';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('moderationResults').innerHTML = 
                `<div class="label-item error">Error: ${error.message}</div>`;
        });
}

// Update results every 500ms
setInterval(updateResults, 500);