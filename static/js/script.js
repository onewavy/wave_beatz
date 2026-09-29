document.addEventListener("DOMContentLoaded", function () {

    // =========================================================
    // WAVE BEATZ - DJ WAVY
    // Stage 6.4 Catalogue + Player
    // =========================================================


    // =========================================================
    // GLOBAL STATE
    // =========================================================

    let beats = [];

    let currentBeatIndex = -1;


    // =========================================================
    // PLAYER ELEMENTS
    // =========================================================

    const audio =
        document.getElementById("audioPlayer");

    const player =
        document.getElementById("player");

    const playerTitle =
        document.getElementById("playerTitle");

    const playerArtist =
        document.getElementById("playerArtist");

    const playButton =
        document.getElementById("playButton");

    const progress =
        document.getElementById("progress");

    const currentTime =
        document.getElementById("currentTime");

    const duration =
        document.getElementById("duration");

    const volume =
        document.getElementById("volume");

    const miniCover =
        document.getElementById("miniCover");


    // =========================================================
    // HELPER
    // =========================================================

    function formatTime(seconds) {

        if (!Number.isFinite(seconds)) {
            return "0:00";
        }

        const mins =
            Math.floor(seconds / 60);

        const secs =
            Math.floor(seconds % 60);

        return (
            mins +
            ":" +
            String(secs).padStart(2, "0")
        );
    }


    // =========================================================
    // LOAD BEATS
    // =========================================================

    async function loadBeats() {

        try {

            const response =
                await fetch("/api/beats");

            if (!response.ok) {
                throw new Error(
                    "Failed to load beats."
                );
            }

            const data =
                await response.json();


            beats = data.map(function (beat) {

                return {

                    id: beat.id,

                    title:
                        beat.title || "",

                    genre:
                        beat.genre || "",

                    bpm:
                        beat.bpm || 0,

                    mood:
                        beat.mood || "",

                    music_key:
                        beat.music_key || "",

                    tags:
                        beat.tags || "",

                    producer:
                        beat.producer || "",

                    license_type:
                        beat.license_type || "",

                    duration:
                        beat.duration || 0,

                    featured:
                        Number(beat.featured || 0),

                    dj_wavy_pick:
                        Number(beat.dj_wavy_pick || 0),

                    audio:
                        beat.audio_file
                            ? "/static/" + beat.audio_file
                            : "",

                    artwork:
                        beat.artwork_file
                            ? "/static/images/" + beat.artwork_file
                            : ""

                };

            });


            updatePlayerBeatIndexes();

        } catch (error) {

            console.error(
                "WAVE BEATZ load error:",
                error
            );

        }

    }


    // =========================================================
    // FIND CURRENT BEAT
    // =========================================================

    function findBeatIndex(title, audioUrl) {

        return beats.findIndex(function (beat) {

            const titleMatch =
                title &&
                beat.title.toLowerCase() ===
                String(title).toLowerCase();

            const audioMatch =
                audioUrl &&
                beat.audio === audioUrl;

            return titleMatch || audioMatch;

        });

    }


    // =========================================================
    // PLAY BEAT
    // =========================================================

    window.playBeat = function (
        title,
        audioUrl
    ) {

        if (!audio) {
            return;
        }


        let index =
            findBeatIndex(
                title,
                audioUrl
            );


        if (index === -1) {

            index =
                beats.findIndex(function (beat) {

                    return (
                        beat.title === title
                    );

                });

        }


        if (index === -1) {

            console.warn(
                "Beat not found:",
                title
            );

            return;

        }


        currentBeatIndex =
            index;


        const beat =
            beats[currentBeatIndex];


        audio.src =
            beat.audio || audioUrl;


        audio.load();


        if (playerTitle) {

            playerTitle.textContent =
                beat.title;

        }


        if (playerArtist) {

            playerArtist.textContent =
                "DJ WAVY • " +
                (
                    beat.genre ||
                    "WAVE BEATZ"
                );

        }


        if (
            miniCover &&
            beat.artwork
        ) {

            miniCover.src =
                beat.artwork;

        }


        if (player) {

            player.classList.add(
                "active"
            );

        }


        updatePlayerBeatIndexes();


        audio.play()
            .then(function () {

                updatePlayButton();

            })
            .catch(function (error) {

                console.error(
                    "Playback error:",
                    error
                );

                updatePlayButton();

            });

    };


    // =========================================================
    // UPDATE PLAYER INDEX
    // =========================================================

    function updatePlayerBeatIndexes() {

        if (
            currentBeatIndex >=
            beats.length
        ) {

            currentBeatIndex =
                beats.length - 1;

        }

    }


    // =========================================================
    // TOGGLE PLAY
    // =========================================================

    window.togglePlay = function () {

        if (!audio) {
            return;
        }


        if (!audio.src) {

            if (beats.length > 0) {

                playBeat(
                    beats[0].title,
                    beats[0].audio
                );

            }

            return;

        }


        if (audio.paused) {

            audio.play()
                .then(function () {

                    updatePlayButton();

                })
                .catch(function (error) {

                    console.error(
                        "Playback error:",
                        error
                    );

                });

        } else {

            audio.pause();

            updatePlayButton();

        }

    };


    // =========================================================
    // PLAY BUTTON
    // =========================================================

    function updatePlayButton() {

        if (!playButton) {
            return;
        }


        if (
            audio &&
            !audio.paused
        ) {

            playButton.textContent =
                "❚❚";

            playButton.setAttribute(
                "aria-label",
                "Pause"
            );

        } else {

            playButton.textContent =
                "▶";

            playButton.setAttribute(
                "aria-label",
                "Play"
            );

        }

    }


    // =========================================================
    // STOP
    // =========================================================

    window.stopBeat = function () {

        if (!audio) {
            return;
        }


        audio.pause();

        audio.currentTime = 0;


        if (progress) {

            progress.value = 0;

        }


        if (currentTime) {

            currentTime.textContent =
                "0:00";

        }


        updatePlayButton();

    };


    // =========================================================
    // NEXT
    // =========================================================

    window.nextBeat = function () {

        if (!beats.length) {
            return;
        }


        if (
            currentBeatIndex < 0
        ) {

            currentBeatIndex = 0;

        } else {

            currentBeatIndex =
                (
                    currentBeatIndex + 1
                ) % beats.length;

        }


        const beat =
            beats[currentBeatIndex];


        playBeat(
            beat.title,
            beat.audio
        );

    };


    // =========================================================
    // PREVIOUS
    // =========================================================

    window.previousBeat = function () {

        if (!beats.length) {
            return;
        }


        if (
            currentBeatIndex < 0
        ) {

            currentBeatIndex =
                beats.length - 1;

        } else {

            currentBeatIndex =
                (
                    currentBeatIndex - 1 +
                    beats.length
                ) % beats.length;

        }


        const beat =
            beats[currentBeatIndex];


        playBeat(
            beat.title,
            beat.audio
        );

    };


    // =========================================================
    // AUDIO EVENTS
    // =========================================================

    if (audio) {


        audio.addEventListener(
            "loadedmetadata",
            function () {

                if (
                    Number.isFinite(
                        audio.duration
                    )
                ) {

                    if (progress) {

                        progress.max =
                            audio.duration;

                    }


                    if (duration) {

                        duration.textContent =
                            formatTime(
                                audio.duration
                            );

                    }

                }

            }
        );


        audio.addEventListener(
            "timeupdate",
            function () {

                if (
                    Number.isFinite(
                        audio.duration
                    )
                ) {

                    if (progress) {

                        progress.value =
                            audio.currentTime;

                    }


                    if (currentTime) {

                        currentTime.textContent =
                            formatTime(
                                audio.currentTime
                            );

                    }

                }

            }
        );


        audio.addEventListener(
            "play",
            updatePlayButton
        );


        audio.addEventListener(
            "pause",
            updatePlayButton
        );


        audio.addEventListener(
            "ended",
            function () {

                if (progress) {

                    progress.value = 0;

                }


                if (currentTime) {

                    currentTime.textContent =
                        "0:00";

                }


                if (beats.length > 1) {

                    nextBeat();

                } else {

                    updatePlayButton();

                }

            }
        );

    }


    // =========================================================
    // PROGRESS BAR
    // =========================================================

    if (progress) {

        progress.addEventListener(
            "input",
            function () {

                if (audio) {

                    audio.currentTime =
                        Number(
                            progress.value
                        );

                }

            }
        );

    }


    // =========================================================
    // VOLUME
    // =========================================================

    if (volume) {

        volume.addEventListener(
            "input",
            function () {

                if (audio) {

                    audio.volume =
                        Number(
                            volume.value
                        );

                }

            }
        );

    }


    if (audio) {

        audio.volume = 1;

    }


    // =========================================================
    // SEARCH
    // =========================================================

    window.searchBeats = function () {

        const input =
            document.getElementById(
                "searchInput"
            );


        const grid =
            document.getElementById(
                "beatGrid"
            );


        if (!input || !grid) {
            return;
        }


        const query =
            input.value
                .trim()
                .toLowerCase();


        const cards =
            grid.querySelectorAll(
                ".beat-card"
            );


        let visibleCount = 0;


        cards.forEach(function (card) {

            const searchableText = [

                card.dataset.name || "",

                card.dataset.genre || "",

                card.dataset.bpm || "",

                card.dataset.key || "",

                card.dataset.mood || "",

                card.dataset.tags || "",

                card.dataset.producer || ""

            ]
                .join(" ")
                .toLowerCase();


            const matches =
                !query ||
                searchableText.includes(
                    query
                );


            if (matches) {

                card.style.display = "";

                visibleCount++;

            } else {

                card.style.display =
                    "none";

            }

        });


        updateSearchEmptyState(
            grid,
            visibleCount,
            query
        );

    };


    // =========================================================
    // SEARCH EMPTY STATE
    // =========================================================

    function updateSearchEmptyState(
        grid,
        visibleCount,
        query
    ) {

        let message =
            grid.querySelector(
                ".search-empty-state"
            );


        if (
            visibleCount === 0 &&
            query
        ) {

            if (!message) {

                message =
                    document.createElement(
                        "div"
                    );

                message.className =
                    "empty-state search-empty-state";

                message.innerHTML = `

                    <div class="empty-icon">
                        ⌕
                    </div>

                    <h3>
                        NO MATCHES FOUND
                    </h3>

                    <p>
                        Try another beat title,
                        genre, mood, key or producer.
                    </p>

                `;

                grid.appendChild(
                    message
                );

            }

        } else {

            if (message) {

                message.remove();

            }

        }

    }


    // =========================================================
    // SORTING
    // =========================================================

    window.sortBeats = function () {

        const select =
            document.getElementById(
                "sortSelect"
            );


        const grid =
            document.getElementById(
                "beatGrid"
            );


        if (!select || !grid) {
            return;
        }


        const sortType =
            select.value;


        const cards =
            Array.from(
                grid.querySelectorAll(
                    ".beat-card"
                )
            );


        cards.sort(function (a, b) {

            switch (sortType) {


                // ---------------------------------------------
                // NEWEST
                // ---------------------------------------------

                case "newest": {

                    const aId =
                        Number(
                            a.dataset.id || 0
                        );

                    const bId =
                        Number(
                            b.dataset.id || 0
                        );

                    return bId - aId;

                }


                // ---------------------------------------------
                // TITLE
                // ---------------------------------------------

                case "title": {

                    const aTitle =
                        (
                            a.dataset.name ||
                            ""
                        ).toLowerCase();


                    const bTitle =
                        (
                            b.dataset.name ||
                            ""
                        ).toLowerCase();


                    return aTitle.localeCompare(
                        bTitle
                    );

                }


                // ---------------------------------------------
                // BPM LOW → HIGH
                // ---------------------------------------------

                case "bpm-low": {

                    const aBpm =
                        Number(
                            a.dataset.bpm || 0
                        );

                    const bBpm =
                        Number(
                            b.dataset.bpm || 0
                        );

                    return aBpm - bBpm;

                }


                // ---------------------------------------------
                // BPM HIGH → LOW
                // ---------------------------------------------

                case "bpm-high": {

                    const aBpm =
                        Number(
                            a.dataset.bpm || 0
                        );

                    const bBpm =
                        Number(
                            b.dataset.bpm || 0
                        );

                    return bBpm - aBpm;

                }


                default:

                    return 0;

            }

        });


        cards.forEach(function (card) {

            grid.appendChild(card);

        });


        // Re-apply search after sorting.

        searchBeats();

    };


    // =========================================================
    // DOWNLOAD
    // =========================================================

    window.downloadBeat = function (
        audioUrl
    ) {

        if (!audioUrl) {

            console.warn(
                "No audio file available."
            );

            return;

        }


        const link =
            document.createElement(
                "a"
            );


        link.href =
            audioUrl;

        link.download = "";


        document.body.appendChild(
            link
        );


        link.click();


        link.remove();

    };


    // =========================================================
    // MOBILE MENU
    // =========================================================

    window.toggleMenu = function () {

        const nav =
            document.getElementById(
                "mainNav"
            );


        const button =
            document.getElementById(
                "menuToggle"
            );


        if (!nav) {
            return;
        }


        nav.classList.toggle(
            "active"
        );


        if (button) {

            button.classList.toggle(
                "active"
            );

        }

    };


    // =========================================================
    // CLOSE MOBILE MENU AFTER LINK CLICK
    // =========================================================

    document.addEventListener(
        "click",
        function (event) {

            const nav =
                document.getElementById(
                    "mainNav"
                );


            const menuButton =
                document.getElementById(
                    "menuToggle"
                );


            if (
                !nav ||
                !menuButton
            ) {
                return;
            }


            if (
                event.target.closest(
                    ".main-nav a"
                )
            ) {

                nav.classList.remove(
                    "active"
                );

                menuButton.classList.remove(
                    "active"
                );

            }

        }
    );


    // =========================================================
    // KEYBOARD PLAYER CONTROLS
    // =========================================================

    document.addEventListener(
        "keydown",
        function (event) {

            const tag =
                event.target.tagName
                    .toLowerCase();


            if (
                tag === "input" ||
                tag === "textarea" ||
                tag === "select"
            ) {

                return;

            }


            // SPACE = PLAY / PAUSE

            if (
                event.code === "Space"
            ) {

                event.preventDefault();

                togglePlay();

            }


            // ARROW RIGHT = NEXT

            if (
                event.code === "ArrowRight"
            ) {

                nextBeat();

            }


            // ARROW LEFT = PREVIOUS

            if (
                event.code === "ArrowLeft"
            ) {

                previousBeat();

            }


            // ESC = STOP

            if (
                event.code === "Escape"
            ) {

                stopBeat();

            }

        }
    );


    // =========================================================
    // INITIALIZE
    // =========================================================

    loadBeats();

    updatePlayButton();

});
