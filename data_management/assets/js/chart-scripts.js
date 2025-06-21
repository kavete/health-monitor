// Chart.js chart instances
let temperatureChartInstance = null;
let humidityChartInstance = null;
let noiseChartInstance = null;
let lightChartInstance = null;

function renderCharts() {
  console.log("renderCharts() called");
  const chartDataScript = document.getElementById("chart-data");
  if (!chartDataScript) {
    console.log("Chart data script not found");
    return;
  }

  let data;
  try {
    const jsonText = chartDataScript.textContent.trim();
    console.log("Raw chart data:", jsonText);
    data = JSON.parse(jsonText);
    console.log("Parsed chart data:", data);
  } catch (e) {
    console.error("Error parsing chart data:", e);
    console.error("Raw content:", chartDataScript.textContent);
    return;
  }

  const tempCtx = document.getElementById("temperatureChart");
  const humCtx = document.getElementById("humidityChart");
  const noiseCtx = document.getElementById("noiseChart");
  const lightCtx = document.getElementById("lightChart");

  console.log("Canvas elements found:", {
    temperature: !!tempCtx,
    humidity: !!humCtx,
    noise: !!noiseCtx,
    light: !!lightCtx,
  });

  if (!tempCtx || !humCtx || !noiseCtx || !lightCtx) {
    console.log("Chart canvas elements not found");
    return;
  }

  // If charts already exist, just update the data
  if (
    temperatureChartInstance &&
    humidityChartInstance &&
    noiseChartInstance &&
    lightChartInstance
  ) {
    console.log("Updating existing charts");
    temperatureChartInstance.data.labels = data.wards;
    temperatureChartInstance.data.datasets[0].data = data.temperature;
    temperatureChartInstance.update("none");

    humidityChartInstance.data.labels = data.wards;
    humidityChartInstance.data.datasets[0].data = data.humidity;
    humidityChartInstance.update("none");

    noiseChartInstance.data.labels = data.wards;
    noiseChartInstance.data.datasets[0].data = data.noise || [];
    noiseChartInstance.update("none");

    lightChartInstance.data.labels = data.wards;
    lightChartInstance.data.datasets[0].data = data.light_intensity || [];
    lightChartInstance.update("none");

    console.log("Charts updated with new data");
    return;
  }

  console.log("Creating charts with data:", data);
  console.log("Noise data specifically:", data.noise);
  console.log("Light intensity data specifically:", data.light_intensity);

  // Create temperature chart
  temperatureChartInstance = new Chart(tempCtx, {
    type: "bar",
    data: {
      labels: data.wards,
      datasets: [
        {
          label: "Temperature (°C)",
          data: data.temperature,
          backgroundColor: "rgba(239, 68, 68, 0.6)",
          borderColor: "rgb(239, 68, 68)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        y: {
          beginAtZero: false,
          title: {
            display: true,
            text: "Temperature (°C)",
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });

  // Create humidity chart
  humidityChartInstance = new Chart(humCtx, {
    type: "bar",
    data: {
      labels: data.wards,
      datasets: [
        {
          label: "Humidity (%)",
          data: data.humidity,
          backgroundColor: "rgba(59, 130, 246, 0.6)",
          borderColor: "rgb(59, 130, 246)",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: "Humidity (%)",
          },
        },
      },
      plugins: {
        legend: {
          display: false,
        },
      },
    },
  });

  // Create noise chart
  try {
    noiseChartInstance = new Chart(noiseCtx, {
      type: "bar",
      data: {
        labels: data.wards,
        datasets: [
          {
            label: "Noise Level (dB)",
            data: data.noise || [],
            backgroundColor: "rgba(168, 85, 247, 0.6)",
            borderColor: "rgb(168, 85, 247)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Noise Level (dB)",
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
        },
      },
    });
    console.log("Noise chart created successfully");
  } catch (error) {
    console.error("Error creating noise chart:", error);
  }

  // Create light intensity chart
  try {
    lightChartInstance = new Chart(lightCtx, {
      type: "bar",
      data: {
        labels: data.wards,
        datasets: [
          {
            label: "Light Intensity (lux)",
            data: data.light_intensity || [],
            backgroundColor: "rgba(251, 191, 36, 0.6)",
            borderColor: "rgb(251, 191, 36)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: "Light Intensity (lux)",
            },
          },
        },
        plugins: {
          legend: {
            display: false,
          },
        },
      },
    });
    console.log("Light intensity chart created successfully");
  } catch (error) {
    console.error("Error creating light intensity chart:", error);
  }

  console.log("Charts created successfully");
}

function updateChartData(newData) {
  if (
    temperatureChartInstance &&
    humidityChartInstance &&
    noiseChartInstance &&
    lightChartInstance
  ) {
    console.log("Updating charts with new data:", newData);

    temperatureChartInstance.data.labels = newData.wards;
    temperatureChartInstance.data.datasets[0].data = newData.temperature;
    temperatureChartInstance.update("none");

    humidityChartInstance.data.labels = newData.wards;
    humidityChartInstance.data.datasets[0].data = newData.humidity;
    humidityChartInstance.update("none");

    noiseChartInstance.data.labels = newData.wards;
    noiseChartInstance.data.datasets[0].data = newData.noise || [];
    noiseChartInstance.update("none");

    lightChartInstance.data.labels = newData.wards;
    lightChartInstance.data.datasets[0].data = newData.light_intensity || [];
    lightChartInstance.update("none");

    // Update the chart data script element for consistency
    const chartDataScript = document.getElementById("chart-data");
    if (chartDataScript) {
      chartDataScript.textContent = JSON.stringify(newData);
    }
  }
}

// Initial render on page load
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", renderCharts);
} else {
  renderCharts();
}

// Function to fetch and update chart data
async function fetchAndUpdateCharts() {
  try {
    console.log("Fetching chart data...");
    const response = await fetch("/dashboard/htmx-charts-json/");

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const newData = await response.json();
    console.log("Fetched chart data:", newData);

    updateChartData(newData);
  } catch (error) {
    console.error("Error fetching chart data:", error);
  }
}

// Set up periodic chart updates every 2 seconds
setInterval(fetchAndUpdateCharts, 2000);
