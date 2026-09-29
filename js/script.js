const audioPlayer = document.getElementById("audioPlayer");
const player = document.getElementById("player");
const playerTitle = document.getElementById("playerTitle");


function playBeat(name, file) {

    playerTitle.textContent = name;

    audioPlayer.src = file;

    player.classList.add("active");

    audioPlayer.play().catch(() => {
        console.log("Audio waiting for user interaction.");
    });
}


function downloadBeat(file) {

    const link = document.createElement("a");

    link.href = file;

    link.download = "";

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
}


function filterBeats(category) {

    const cards =
        document.querySelectorAll(".beat-card");

    cards.forEach(card => {

        const genre =
            card.dataset.genre;

        if (category === "all" || genre === category) {

            card.style.display = "";

        } else {

            card.style.display = "none";

        }

    });

}


function searchBeats() {

    const search =
        document
            .getElementById("searchInput")
            .value
            .toLowerCase();

    const cards =
        document.querySelectorAll(".beat-card");

    cards.forEach(card => {

        const name =
            card.dataset.name.toLowerCase();

        if (name.includes(search)) {

            card.style.display = "";

        } else {

            card.style.display = "none";

        }

    });

}


function toggleMenu() {

    const nav =
        document.querySelector(".navbar nav");

    if (nav.style.display === "flex") {

        nav.style.display = "";

    } else {

        nav.style.display = "flex";

        nav.style.position = "absolute";

        nav.style.top = "75px";

        nav.style.left = "0";

        nav.style.width = "100%";

        nav.style.padding = "25px";

        nav.style.background = "#080808";

        nav.style.flexDirection = "column";

    }

}

/* =========================================================
   STAGE 7 — LICENSE SELECTION
========================================================= */

document.addEventListener("DOMContentLoaded", function () {

    const modal = document.getElementById("licenseModal");
    const openButton = document.getElementById("openLicenseButton");
    const requestBox = document.getElementById("licenseRequest");
    const selectedLicense = document.getElementById("selectedLicense");
    const requestText = document.getElementById("licenseRequestText");
    const backButton = document.getElementById("backToLicenseChoices");
    const contactButton = document.getElementById("licenseContactButton");

    if (!modal) {
        return;
    }

    const choices = modal.querySelector(".license-modal-options");

    function openModal() {
        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");
        document.body.classList.add("license-modal-open");
    }

    function closeModal() {
        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");
        document.body.classList.remove("license-modal-open");

        if (requestBox) {
            requestBox.hidden = true;
        }

        if (choices) {
            choices.hidden = false;
        }
    }

    function selectLicense(type) {

        let name = "BASIC LEASE";
        let message = "Contact DJ WAVY to confirm pricing, terms and delivery.";

        if (type === "premium") {
            name = "PREMIUM LEASE";
            message = "Contact DJ WAVY to confirm the Premium Lease pricing, terms and delivery.";
        }

        if (type === "exclusive") {
            name = "EXCLUSIVE";
            message = "Exclusive rights are handled directly with DJ WAVY. Contact DJ WAVY to discuss the agreement.";
        }

        if (selectedLicense) {
            selectedLicense.textContent = name;
        }

        if (requestText) {
            requestText.textContent = message;
        }

        if (choices) {
            choices.hidden = true;
        }

        if (requestBox) {
            requestBox.hidden = false;
        }
    }

    if (openButton) {
        openButton.addEventListener("click", openModal);
    }

    modal.querySelectorAll("[data-open-license]").forEach(function (button) {

        button.addEventListener("click", function () {

            const type = button.getAttribute("data-open-license");

            openModal();
            selectLicense(type);

        });

    });

    modal.querySelectorAll("[data-close-license]").forEach(function (button) {

        button.addEventListener("click", closeModal);

    });

    if (backButton) {

        backButton.addEventListener("click", function () {

            if (requestBox) {
                requestBox.hidden = true;
            }

            if (choices) {
                choices.hidden = false;
            }

        });

    }

    document.addEventListener("keydown", function (event) {

        if (event.key === "Escape") {
            closeModal();
        }

    });

    /*
       Contact action is intentionally left without
       a fake payment/contact address.
       We will connect the real DJ WAVY contact/payment
       method in the next licensing step.
    */

    if (contactButton) {

        contactButton.addEventListener("click", function (event) {

            event.preventDefault();

            alert(
                "License request selected. DJ WAVY contact and payment will be connected next."
            );

        });

    }

});
