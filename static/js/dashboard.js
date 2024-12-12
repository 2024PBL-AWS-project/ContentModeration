import { moderationService } from "./moderationService.js";
import { MODERATION_CATEGORIES } from "./moderationConfig.js";

let moderationChart;
let alertCount = 0;
let totalFrames = 0;

function initializeChart() {
  const ctx = document.getElementById("moderationChart").getContext("2d");
  moderationChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: [],
      datasets: MODERATION_CATEGORIES.map((category) => ({
        label: category.label,
        borderColor: category.borderColor,
        data: [],
        fill: false,
      })),
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: "Confidence Level (%)",
          },
        },
      },
      animation: {
        duration: 0,
      },
    },
  });
}

function updateDashboard(moderationData) {
  if (!moderationChart) {
    initializeChart();
  }

  console.log("Updating dashboard with data:", moderationData);

  const timestamp = new Date().toLocaleTimeString();

  // 각 카테고리별 신뢰도 초기화
  const confidences = {};
  MODERATION_CATEGORIES.forEach((category) => {
    confidences[category.label] = 0;
  });

  // 각 카테고리별 최대 신뢰도 찾기
  moderationData.forEach((label) => {
    MODERATION_CATEGORIES.forEach((category) => {
      if (label.Name === category.label) {
        confidences[category.label] = Math.max(
          confidences[category.label],
          label.Confidence
        );
      }
    });
  });

  // 알림 조건 확인
  if (
    MODERATION_CATEGORIES.some(
      (category) => confidences[category.label] > category.threshold
    )
  ) {
    alertCount++;
    document.getElementById("alertCount").textContent = `Alerts: ${alertCount}`;
  }

  // 차트 데이터 업데이트
  moderationChart.data.labels.push(timestamp);
  moderationChart.data.datasets.forEach((dataset, index) => {
    const categoryLabel = MODERATION_CATEGORIES[index].label;
    dataset.data.push(confidences[categoryLabel]);
  });

  // Keep only last 20 data points
  if (moderationChart.data.labels.length > 20) {
    moderationChart.data.labels.shift();
    moderationChart.data.datasets.forEach((dataset) => dataset.data.shift());
  }

  moderationChart.update();
}

// Listen for moderation updates
window.addEventListener(moderationService.EVENT_NAME, (event) => {
  const latestResult = event.detail;
  totalFrames++;
  document.getElementById(
    "totalFrames"
  ).textContent = `Total Frames: ${totalFrames}`;

  if (latestResult.labels) {
    updateDashboard(latestResult.labels);
  }
});

// Initialize chart when page loads
document.addEventListener("DOMContentLoaded", initializeChart);
