$(function() {
    // Alapértelmezett config / localstorage betöltés a clockhoz    
    if (localStorage.getItem('active') !== null) {
        if (localStorage.getItem('active') == 1) {
            setActive = true;            
        } else {
            setActive = false;
        }
    } else {
        setActive = false;
    }

    if (localStorage.getItem('jobActive') !== null) {
        if (localStorage.getItem('jobActive') == 1) {
            setJobActive = true;            
        } else {
            setJobActive = false;
        }
    } else {
        setJobActive = false;
    }

    if (localStorage.getItem('type') !== null) {        
        if (localStorage.getItem('type') == "Break") {
            setType = "Break";
        } else {
            setType = "Session";
        }
    } else {
        setType = "Session";
    }

    if (localStorage.getItem('startTime') !== null) {
        setStartTime = parseInt(localStorage.getItem('startTime'));
    } else {
        setStartTime = 1500;
    }

    if (localStorage.getItem('currentTime') !== null) {
        setCurrentTime = parseInt(localStorage.getItem('currentTime'));
    } else {
        setCurrentTime = 1500;
    }

    if (localStorage.getItem('sessionTime') !== null) {
        setSessionTime = parseInt(localStorage.getItem('sessionTime'));
    } else {
        setSessionTime = 1500;
    }

    if (localStorage.getItem('breakTime') !== null) {
        setBreakTime = parseInt(localStorage.getItem('breakTime'));
    } else {
        setBreakTime = 300;
    }    
    
    if (localStorage.getItem('sessionCount') !== null) {
        setSessionCount = parseInt(localStorage.getItem('sessionCount'));
    } else {
        setSessionCount = 0;
    }

    if (localStorage.getItem('jobTime') !== null) {
        setJobTime = parseInt(localStorage.getItem('jobTime'));
    } else {
        setJobTime = 0;
    }

    // Inicializálás
    var clock = new Clock();
    if (setActive == true) {
        clock.toggleClock();
        clock.toggleClock();
    }  
    
    clock.displayCurrentTime();
    clock.displaySessionTime();
    clock.displayBreakTime();
    clock.displaySessionCount();    
    
    // Esemény kezelők hozzáadása
    $(".time-session .minus").click(function() {
        clock.changeSessionTime("subtract");
    });
    $(".time-session .plus").click(function() {
        clock.changeSessionTime("add");
    });
    $(".time-break .minus").click(function() {
        clock.changeBreakTime("subtract");
    });
    $(".time-break .plus").click(function() {
        clock.changeBreakTime("add");
    });
    $(".time-start").click(function() {
        clock.toggleClock();
    });
    $(".time-reset").click(function() {
        clock.reset();
    });
    $(".startJobButton").click(function() {
        clock.startActiveJob();
    });
    $(".endJobButton").click(function() {        
        clock.endActiveJob();
    });

        
    // Clock metódusokkal és változókkal
    function Clock() {      
        var _this = this, 
        timer,
        active = setActive, // Fut-e az óra
        type = setType, // Munka vagy szünet
        startTime = setStartTime, // Kezdő idő hossza
        currentTime = setCurrentTime, //  Aktuális idő az órán
        sessionTime = setSessionTime, // Munkamenet idő seconds
        breakTime = setBreakTime, // Szünet idő seconds
        sessionCount = setSessionCount, // Munkamenetek száma
        jobActive  = setJobActive // Aktív feladat mérés van-e
        jobTime  = setJobTime // Aktív feladat mérés
        startAudio  = document.getElementById("startAudio"); 
        endAudio  = document.getElementById("endAudio");
        
        // Mentés  
        localStorage.setItem('active', (active == true ? 1 : 0) );
        localStorage.setItem('jobActive', (jobActive == true ? 1 : 0) );
        localStorage.setItem('type', type);
        localStorage.setItem('startTime', startTime);
        localStorage.setItem('currentTime', currentTime);
        localStorage.setItem('sessionTime', sessionTime);
        localStorage.setItem('breakTime', breakTime);
        localStorage.setItem('sessionCount', sessionCount);
        localStorage.setItem('jobTime', jobTime);

        // Formázás  
        function formatTime(secs) {
            var result = "";
            var seconds = secs % 60;
            var minutes = parseInt(secs / 60) % 60;
            var hours = parseInt(secs / 3600);
            function addLeadingZeroes(time) {
            return time < 10 ? "0" + time : time;
            }
            if (hours > 0) result += (hours + ":");
            result += (addLeadingZeroes(minutes) + ":" + addLeadingZeroes(seconds));
            return result;
        }
        
        // Aktív munka kezelés
        this.startActiveJob = function() {
            jobActive = true;
            jobTime = 0;
            localStorage.setItem('jobActive', 1);
            localStorage.setItem('jobTime', 0);
            if (active === false) {
                this.toggleClock();
            }
        }
        this.endActiveJob = function() {
            jobActive = false;
            jobTime = 0;
            localStorage.setItem('jobActive', 0);
            localStorage.setItem('jobTime', 0);
            if (active === true) {
                this.toggleClock();
            }
        }
      
        // Munkamenet hossz beállítása      
        this.changeSessionTime = function(str) {
            if (active === false) {
                this.reset();
            if (str === "add") {
                sessionTime += 60;            
            } else if ( sessionTime > 60){
                sessionTime -= 60;
            }
            currentTime = sessionTime;
            startTime = sessionTime;
            localStorage.setItem('sessionTime', sessionTime);
            localStorage.setItem('currentTime', sessionTime);
            localStorage.setItem('startTime', sessionTime);
            this.displaySessionTime();
            this.displayCurrentTime();
            }
        }
      
        // Szünet hossz beállítása
        this.changeBreakTime = function(str) {
            if (active === false) {
                this.reset();
                if (str === "add") {
                    breakTime += 60;
                } else if (breakTime > 60) {
                    breakTime -= 60;
                }
                localStorage.setItem('breakTime', breakTime);
                this.displayBreakTime();
            }
        }
        
        // Megjelenítés
        this.displayCurrentTime = function() {
            $('.main-display').text(formatTime(currentTime));
            if (type === "Session" && $('.progress-radial').hasClass('break')) {
                $('.progress-radial').removeClass('break').addClass('session');
            } else if (type === "Break" && $('.progress-radial').hasClass('session')) {
                $('.progress-radial').removeClass('session').addClass('break');
            }
            $('.progress-radial').attr('class', function(i, c) {
                return c.replace(/(^|\s)step-\S+/g, " step-" + (100 - parseInt((currentTime / startTime) * 100)));
            });
        }

        this.displayCurrentJobTime = function() {
            $('.activeJobDisplay').text(formatTime(jobTime));
        }
      
        this.displaySessionTime = function() {
            $('.time-session .time-session-display').text(parseInt(sessionTime / 60) + " perc");
        }
      
        this.displayBreakTime = function() {
            $('.time-break .time-break-display').text(parseInt(breakTime / 60) + " perc");
        }
      
        this.displaySessionCount = function() {
            if (sessionCount === 0) {
                $('.session-count').html("<h2 class=\"timer-h\">Nincs mérés</h2>");
            } else if (type === "Session") {
                $('.session-count').html("<h2 class=\"timer-h\">Munka " + sessionCount + "</h2>"); 
            } else if (type === "Break") {
                $('.session-count').html("<h2 class=\"timer-h\">Szünet!</h2>");
            }
        }
      
        // Indítás / Megállítás
        this.toggleClock = function() {
            if (active === true ) {
                clearInterval(timer);
                $('.time-start').text('Indítás');
                active = false;
                localStorage.setItem('active', 0);
            } else {
                $('.time-start').text('Megállítás');
                if (sessionCount === 0) {
                    sessionCount = 1;
                    localStorage.setItem('sessionCount', sessionCount);
                    this.displaySessionCount();
                    startAudio.play();
                }
                timer = setInterval(function() {
                    _this.stepDown();
                }, 1000);
                active = true;
                localStorage.setItem('active', 1);
            }
        }
      
        // Óra tick 
        this.stepDown = function() {
            if (currentTime > 0) {
                currentTime --;
                if (jobActive === true) {
                    jobTime ++;
                    localStorage.setItem('jobTime', jobTime);
                    this.displayCurrentJobTime();
                }
                localStorage.setItem('currentTime', currentTime);
                this.displayCurrentTime();
                if (currentTime === 0) {
                    if (type === "Session") {
                        currentTime = breakTime;
                        startTime = breakTime;
                        type = "Break";
                        localStorage.setItem('currentTime', currentTime);
                        localStorage.setItem('startTime', startTime);
                        localStorage.setItem('type', type);
                        this.displaySessionCount();
                        endAudio.play();
                    } else {
                        sessionCount ++;              
                        currentTime = sessionTime;
                        startTime = sessionTime;
                        type = "Session";
                        localStorage.setItem('sessionCount', sessionCount);
                        localStorage.setItem('currentTime', currentTime);
                        localStorage.setItem('startTime', startTime);
                        localStorage.setItem('type', type);
                        this.displaySessionCount();
                        startAudio.play();
                    }
                }
            }
        }
        
        // Reset az órát
        this.reset = function() {
            clearInterval(timer);
            active = false;
            type = "Session";
            currentTime = sessionTime;
            sessionCount = 0;
            localStorage.setItem('active', 0);
            localStorage.setItem('type', type);
            localStorage.setItem('currentTime', currentTime);
            localStorage.setItem('sessionCount', sessionCount);
            $('.time-start').text('Indítás');
            this.displayCurrentTime();
            this.displaySessionTime();
            this.displaySessionCount();
        }
    } // Clock
});