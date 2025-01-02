class ModerationService {
  constructor() {
    this.EVENT_NAME = "moderationUpdate";
    this.errorCount = 0;
    this.maxErrors = 5;
    this.intervalId = null;
    this.startFetching();
  }

  startFetching() {
    this.intervalId = setInterval(() => {
      fetch("/get_results")
        .then((response) => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then((data) => {
          this.errorCount = 0;
          if (data && data.length > 0) {
            const latestResult = data[0];
            console.log("/get_results success > ", latestResult);

            const event = new CustomEvent(this.EVENT_NAME, {
              detail: latestResult,
            });
            window.dispatchEvent(event);
          }
        })
        .catch((error) => {
          console.error("Error fetching results:", error);
          this.errorCount++;
          if (this.errorCount >= this.maxErrors) {
            console.warn("Max error count reached, stopping interval.");
            clearInterval(this.intervalId);
          }
        });
    }, 1000);
  }
}

export const moderationService = new ModerationService();
