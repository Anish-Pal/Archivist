"use strict";


const themeToggle = document.getElementById("themeToggle");

function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("archivist-theme", theme);
}

function initTheme() {
    const saved = localStorage.getItem("archivist-theme");
    if (saved) {
        applyTheme(saved);
        return;
    }
    const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
    applyTheme(prefersLight ? "light" : "dark");
}

themeToggle.addEventListener("click", function () {
    const current = document.documentElement.getAttribute("data-theme");
    applyTheme(current === "dark" ? "light" : "dark");
});

initTheme();

/* =========================================================
   Step timeline — reveal steps one by one on page load
   ========================================================= */

function revealSteps() {
    const steps = document.querySelectorAll("#stepTimeline .step");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    steps.forEach(function (step, index) {
        const delay = prefersReducedMotion ? 0 : index * 180;
        setTimeout(function () {
            step.classList.add("is-visible");
        }, delay);
    });
}

revealSteps();

/* =========================================================
   Indexing card — swaps label text in sync with the CSS
   progress-bar loop (see fill-loop animation, 4s cycle)
   ========================================================= */

function cycleIndexingLabel() {
    const label = document.getElementById("indexingLabel");
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!label || prefersReducedMotion) {
        return;
    }

    const states = [
        "Indexing quarterly_report.pdf…",
        "✓ Indexed successfully"
    ];
    let index = 0;

    setInterval(function () {
        label.style.opacity = "0";

        setTimeout(function () {
            index = (index + 1) % states.length;
            label.textContent = states[index];
            label.style.opacity = "1";
        }, 250);

    }, 2800);
}

cycleIndexingLabel();

/* =========================================================
   Signup form
   ========================================================= */


const signupForm = document.getElementById("signupForm");
const usernameInput = document.getElementById("username");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const confirmPasswordInput = document.getElementById("confirmPassword");
const authError = document.getElementById("authError");


function showError(message){

    authError.textContent = message;

    authError.classList.add("is-visible");
}

function clearError() {

    authError.textContent = "";

    authError.classList.remove("is-visible");
}


signupForm.addEventListener("submit" , async function(event){

    event.preventDefault();

    clearError();

    const username = usernameInput.value.trim();
    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmPasswordInput.value;

    usernameInput.classList.remove("field--invalid");
    emailInput.classList.remove("field--invalid");
    passwordInput.classList.remove("field--invalid");
    confirmPasswordInput.classList.remove("field--invalid");


    if (!username && !email && !password && !confirmPassword) {

        showError("Please fill in all fields.");

        usernameInput.classList.add("field--invalid");
        emailInput.classList.add("field--invalid");
        passwordInput.classList.add("field--invalid");
        confirmPasswordInput.classList.add("field--invalid");

        return;
    }

    if (!username) {

        showError("Please enter your username.");

        usernameInput.classList.add("field--invalid");

        return;
    }

    if (!email) {

        showError("Please enter your email.");

        emailInput.classList.add("field--invalid");

        return;
    }

    if (!password) {

        showError("Please enter your password.");

        passwordInput.classList.add("field--invalid");

        return;
    }

    if (!confirmPassword) {

        showError("Please confirm your password.");

        confirmPasswordInput.classList.add("field--invalid");

        return;
    }   


    if(password.length < 8){

        showError("Password must be at least 8 characters.");

        passwordInput.classList.add("field--invalid");

        return;
    }

    if (password !== confirmPassword) {

        showError("Passwords don't match.");

        confirmPasswordInput.classList.add("field--invalid");

        return;
    }

    try{
        const response = await fetch("/signup", {
            method : "POST",
            headers : {
                "Content-Type": "application/json",
            },
            body : JSON.stringify({
                username : username,
                email : email,
                password : password
            })
        });

        const data = await response.json();

        if(!response.ok){
            showError(data.detail);
            return;
        }

        window.location.href = "/login"

    } catch(error){

        console.error("Signup request failed:", error);

        showError("Could not reach the server. Please try again.");
        
    }

    
});
