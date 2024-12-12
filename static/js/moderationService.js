class ModerationService {
  constructor() {
    // Custom event for moderation updates
    this.EVENT_NAME = "moderationUpdate";
    this.startFetching();
  }

  startFetching() {
    setInterval(() => {
      fetch("/get_results")
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          if (data && data.length > 0) {
            const latestResult = data[0];
            console.log("/get_results success > ", latestResult);

            // Dispatch custom event with the data
            const event = new CustomEvent(this.EVENT_NAME, {
              detail: latestResult,
            });
            window.dispatchEvent(event);
          }
        })
        .catch((error) => console.error("Error fetching results:", error));
    }, 1000);
  }
}

// Create single instance
export const moderationService = new ModerationService();
