const resendBtn = document.getElementById("resend-btn");

const timerText = document.getElementById("timer-text");


if (resendBtn && timerText && typeof remainingSeconds !== "undefined") {

const resendUrl = resendBtn.dataset.url;


function updateTimer() {

if (remainingSeconds <= 0) {

resendBtn.disabled = false;

timerText.innerText = "You can resend OTP now.";

resendBtn.addEventListener("click", () => {
location.href = resendUrl;
});

return;

}


let minutes = Math.floor(remainingSeconds / 60);

let seconds = remainingSeconds % 60;


timerText.innerText =
"Resend OTP available in " +
minutes.toString().padStart(2, '0') +
":" +
seconds.toString().padStart(2, '0');


remainingSeconds--;


setTimeout(updateTimer, 1000);

}


updateTimer();

}