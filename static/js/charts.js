document.addEventListener('DOMContentLoaded', () => {
    // Score Distribution Chart (Enterprise Minimal Palette)
    const distCanvas = document.getElementById('scoreDistributionChart');
    if (distCanvas && window.distributionData) {
        new Chart(distCanvas, {
            type: 'bar',
            data: {
                labels: ['0-39% (Low)', '40-69% (Moderate)', '70-84% (Strong)', '85-100% (High Conviction)'],
                datasets: [{
                    label: 'Candidates',
                    data: window.distributionData,
                    backgroundColor: [
                        '#FDF1F0',
                        '#FFF8E8',
                        '#EDF2F7',
                        '#E7F0ED'
                    ],
                    borderColor: [
                        '#B85450',
                        '#B7791F',
                        '#4A5568',
                        '#245C59'
                    ],
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1C1C1A',
                        titleFont: { family: 'Inter', size: 12, weight: '600' },
                        bodyFont: { family: 'Inter', size: 12 },
                        padding: 10,
                        cornerRadius: 6
                    }
                },
                scales: {
                    x: {
                        grid: { color: '#E6E5E1', drawBorder: false },
                        ticks: { color: '#6B6F6A', font: { family: 'Inter', size: 11 } }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, color: '#6B6F6A', font: { family: 'Inter', size: 11 } },
                        grid: { color: '#E6E5E1', drawBorder: false }
                    }
                }
            }
        });
    }

    // Candidate Radar Breakdown Chart (for candidate_detail.html)
    const radarCanvas = document.getElementById('candidateScoreRadar');
    if (radarCanvas && window.candidateBreakdown) {
        new Chart(radarCanvas, {
            type: 'radar',
            data: {
                labels: ['Lexical Match', 'Semantic Similarity', 'Skill Overlap'],
                datasets: [{
                    label: 'Match Profile',
                    data: [
                        window.candidateBreakdown.lexical,
                        window.candidateBreakdown.semantic,
                        window.candidateBreakdown.skills
                    ],
                    backgroundColor: 'rgba(36, 92, 89, 0.15)',
                    borderColor: '#245C59',
                    borderWidth: 2,
                    pointBackgroundColor: '#245C59',
                    pointBorderColor: '#FFFFFF',
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: { color: '#E6E5E1' },
                        grid: { color: '#E6E5E1' },
                        pointLabels: {
                            color: '#1C1C1A',
                            font: { family: 'Inter', size: 12, weight: '500' }
                        },
                        suggestedMin: 0,
                        suggestedMax: 100,
                        ticks: { backdropColor: 'transparent', color: '#6B6F6A', stepSize: 25 }
                    }
                },
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }

    // Client-side quick filter for tables
    const searchInput = document.getElementById('tableSearchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            const rows = document.querySelectorAll('.modern-table tbody tr');
            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                row.style.display = text.includes(term) ? '' : 'none';
            });
        });
    }
});
