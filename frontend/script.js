async function getFeedback() {
    try {
        const response = await fetch("http://127.0.0.1:5000/feedback");
        const data = await response.json();

        document.getElementById("message").innerText = data.message;
        document.getElementById("accuracy").innerText = data.accuracy;

        // Optional voice feedback
        if (data.message) {
            speak(data.message);
        }

    } catch (error) {
        console.log("Waiting for backend...");
    }
}

function speak(text) {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    speechSynthesis.speak(utterance);
}

// Fetch feedback every 1 second
setInterval(getFeedback, 1000);
