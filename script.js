let sombreroData = [];
let pilatusData = [];
let sortAscending = true;
let activeNavigator = 'sombrero';
const ITEMS_PER_PAGE = 50;

// Load data for both projects
Promise.all([
    fetch('data/sanitized/ai_google_alerts_cleaned.json').then(res => res.json()),
    fetch('data/sanitized/pilatus_alerts_cleaned.json').then(res => res.json())
])
    .then(([sombrero, pilatus]) => {
        console.log('Loaded Sombrero:', sombrero);
        console.log('Loaded Pilatus:', pilatus);
        sombreroData = sombrero;
        pilatusData = pilatus;
        document.getElementById('sombrero-count').textContent = `(${sombreroData.length})`;
        document.getElementById('pilatus-count').textContent = `(${pilatusData.length})`;
        displayPage('sombrero', 1);
    })
    .catch(error => {
        console.error('Error loading data:', error);
        document.getElementById('sombrero-alerts').innerHTML = '<p>Error loading Sombrero data.</p>';
        document.getElementById('pilatus-alerts').innerHTML = '<p>Error loading Pilatus data.</p>';
    });

// Display alerts for the current page
function displayAlerts(alerts, containerId, page) {
    const alertsDiv = document.getElementById(`${containerId}-alerts`);
    alertsDiv.innerHTML = '';

    if (alerts.length === 0) {
        alertsDiv.innerHTML = '<p>No alerts found.</p>';
        return;
    }

    const start = (page - 1) * ITEMS_PER_PAGE;
    const end = Math.min(start + ITEMS_PER_PAGE, alerts.length);
    const paginatedAlerts = alerts.slice(start, end);

    paginatedAlerts.forEach(alert => {
        const div = document.createElement('div');
        div.className = 'alert';
        const categoryLabel = containerId === 'sombrero' ? 'Category: AI Use Case' : 'Category: AI Risks';
        div.innerHTML = `
            <h3>${alert.title}</h3>
            <a href="${alert.url}" target="_blank">${alert.url}</a>
            <p><strong>Synopsis:</strong> ${alert.synopsis}</p>
            <p><strong>${categoryLabel}</strong></p>
            <p><strong>Date:</strong> ${alert.date}</p>
        `;
        alertsDiv.appendChild(div);
    });

    updatePagination(containerId, page, alerts.length);
}

// Update pagination controls
function updatePagination(containerId, currentPage, totalItems) {
    const paginationDiv = document.getElementById(`${containerId}-pagination`);
    const totalPages = Math.ceil(totalItems / ITEMS_PER_PAGE);

    paginationDiv.innerHTML = `
        <button id="${containerId}-prev" ${currentPage === 1 ? 'disabled' : ''}>Previous</button>
        <span>Page ${currentPage} of ${totalPages}</span>
        <button id="${containerId}-next" ${currentPage === totalPages ? 'disabled' : ''}>Next</button>
    `;

    document.getElementById(`${containerId}-prev`).addEventListener('click', () => displayPage(containerId, currentPage - 1));
    document.getElementById(`${containerId}-next`).addEventListener('click', () => displayPage(containerId, currentPage + 1));
}

// Display a specific page
function displayPage(containerId, page) {
    const data = containerId === 'sombrero' ? sombreroData : pilatusData;
    displayAlerts(data, containerId, page);
}

// Tab switching
document.getElementById('sombrero-tab').addEventListener('click', () => {
    activeNavigator = 'sombrero';
    document.getElementById('sombrero-tab').classList.add('active');
    document.getElementById('pilatus-tab').classList.remove('active');
    document.getElementById('sombrero-container').classList.add('active');
    document.getElementById('pilatus-container').classList.remove('active');
    displayPage('sombrero', 1);
    document.getElementById('search').value = '';
});

document.getElementById('pilatus-tab').addEventListener('click', () => {
    activeNavigator = 'pilatus';
    document.getElementById('pilatus-tab').classList.add('active');
    document.getElementById('sombrero-tab').classList.remove('active');
    document.getElementById('pilatus-container').classList.add('active');
    document.getElementById('sombrero-container').classList.remove('active');
    displayPage('pilatus', 1);
    document.getElementById('search').value = '';
});

// Search functionality
document.getElementById('search').addEventListener('input', function(e) {
    const query = e.target.value.toLowerCase();
    const data = activeNavigator === 'sombrero' ? sombreroData : pilatusData;
    const containerId = activeNavigator === 'sombrero' ? 'sombrero' : 'pilatus';
    const filtered = data.filter(alert => 
        alert.title.toLowerCase().includes(query) || 
        alert.synopsis.toLowerCase().includes(query)
    );
    displayAlerts(filtered, containerId, 1);
});

// Sort by date
document.getElementById('sort-date').addEventListener('click', function() {
    const data = activeNavigator === 'sombrero' ? sombreroData : pilatusData;
    const containerId = activeNavigator === 'sombrero' ? 'sombrero' : 'pilatus';
    const sorted = [...data].sort((a, b) => {
        const dateA = new Date(a.date);
        const dateB = new Date(b.date);
        return sortAscending ? dateA - dateB : dateB - dateA;
    });
    sortAscending = !sortAscending;
    this.textContent = sortAscending ? 'Sort by Date (Oldest First)' : 'Sort by Date (Newest First)';
    if (activeNavigator === 'sombrero') sombreroData = sorted;
    else pilatusData = sorted;
    displayPage(containerId, 1);
});