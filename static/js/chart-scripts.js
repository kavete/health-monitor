// Chart.js chart instances
let temperatureChartInstance = null;
let humidityChartInstance = null;

function renderCharts() {
  const chartDataScript = document.getElementById('chart-data');
  if (!chartDataScript) {
    console.log('Chart data script not found');
    return;
  }
  
  let data;
  try {
    const jsonText = chartDataScript.textContent.trim();
    console.log('Raw chart data:', jsonText);
    data = JSON.parse(jsonText);
    console.log('Parsed chart data:', data);
  } catch (e) {
    console.error('Error parsing chart data:', e);
    console.error('Raw content:', chartDataScript.textContent);
    return;
  }

  const tempCtx = document.getElementById('temperatureChart');
  const humCtx = document.getElementById('humidityChart');
  
  if (!tempCtx || !humCtx) {
    console.log('Chart canvas elements not found');
    return;
  }

  // If charts already exist, just update the data
  if (temperatureChartInstance && humidityChartInstance) {
    console.log('Updating existing charts');
    temperatureChartInstance.data.labels = data.wards;
    temperatureChartInstance.data.datasets[0].data = data.temperature;
    temperatureChartInstance.update('none');
    
    humidityChartInstance.data.labels = data.wards;
    humidityChartInstance.data.datasets[0].data = data.humidity;
    humidityChartInstance.update('none');
    
    console.log('Charts updated with new data');
    return;
  }

  console.log('Creating charts with data:', data);
  
  // Create temperature chart
  temperatureChartInstance = new Chart(tempCtx, {
    type: 'bar',
    data: {
      labels: data.wards,
      datasets: [{
        label: 'Ward Temperature',
        data: data.temperature,
        borderWidth: 1,
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });

  // Create humidity chart
  humidityChartInstance = new Chart(humCtx, {
    type: 'bar',
    data: {
      labels: data.wards,
      datasets: [{
        label: 'Ward Humidity',
        data: data.humidity,
        borderWidth: 1,
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        y: {
          beginAtZero: true
        }
      }
    }
  });
  
  console.log('Charts created successfully');
}

function updateChartData(newData) {
  if (temperatureChartInstance && humidityChartInstance) {
    console.log('Updating charts with new data:', newData);
    
    temperatureChartInstance.data.labels = newData.wards;
    temperatureChartInstance.data.datasets[0].data = newData.temperature;
    temperatureChartInstance.update('none');
    
    humidityChartInstance.data.labels = newData.wards;
    humidityChartInstance.data.datasets[0].data = newData.humidity;
    humidityChartInstance.update('none');
    
    // Update the chart data script element for consistency
    const chartDataScript = document.getElementById('chart-data');
    if (chartDataScript) {
      chartDataScript.textContent = JSON.stringify(newData);
    }
  }
}

// Initial render on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', renderCharts);
} else {
  renderCharts();
}

// Function to fetch and update chart data
async function fetchAndUpdateCharts() {
  try {
    console.log('Fetching chart data...');
    const response = await fetch('/dashboard/htmx-charts-json/');
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const newData = await response.json();
    console.log('Fetched chart data:', newData);
    
    updateChartData(newData);
  } catch (error) {
    console.error('Error fetching chart data:', error);
  }
}

// Set up periodic chart updates every 5 seconds
setInterval(fetchAndUpdateCharts, 5000);