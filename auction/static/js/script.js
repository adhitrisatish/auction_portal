const endTimeElement = document.getElementById("end-time");

if (endTimeElement) {
    const endTime = new Date(endTimeElement.innerText).getTime();

    const timer = setInterval(function () {
        const now = new Date().getTime();
        const distance = endTime - now;

        if (distance <= 0) {
            document.getElementById("timer").innerHTML = "Auction Ended";
            clearInterval(timer);
            return;
        }

        const days = Math.floor(distance / (1000 * 60 * 60 * 24));
        const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((distance % (1000 * 60)) / 1000);

        document.getElementById("timer").innerHTML =
            days + "d " + hours + "h " + minutes + "m " + seconds + "s";
    }, 1000);
}

const searchBox = document.getElementById("searchBox");

if (searchBox) {
    searchBox.addEventListener("keyup", function () {
        let filter = searchBox.value.toLowerCase();
        let cards = document.querySelectorAll(".item-card");

        cards.forEach(function(card) {
            let text = card.innerText.toLowerCase();

            if (text.includes(filter)) {
                card.style.display = "block";
            } else {
                card.style.display = "none";
            }
        });
    });
}

function validateBid() {
    let amount = document.getElementById("amount").value;
    let error = document.getElementById("bidError");

    error.textContent = "";

    if (amount.trim() === "") {
        error.textContent = "Bid amount is required.";
        return false;
    }

    if (isNaN(amount)) {
        error.textContent = "Bid must be a number.";
        return false;
    }

    if (Number(amount) <= 0) {
        error.textContent = "Bid must be greater than 0.";
        return false;
    }

    return true;
}