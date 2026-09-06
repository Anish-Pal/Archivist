"use strict";

const themeToggle = document.getElementById("themeToggle");

function applyTheme(theme){

    document.documentElement.setAttribute(
        "data-theme",
        theme
    );

    localStorage.setItem(
        "archivist-theme",
        theme
    );
}


function initTheme(){

    const saved = localStorage.getItem("archivist-theme");

    if(saved){
        applyTheme(saved);
        return;
    }

    const prefersLight = window.matchMedia("(prefers-color-scheme: dark)").matches;

    applyTheme(
        prefersLight ? "light" : "dark"
    );
}

themeToggle.addEventListener("click" , function(){

    const current = document.documentElement.getAttribute("data-theme");

    const newTheme = current === "dark" ? "light" : "dark";

    applyTheme(newTheme);
});

initTheme();

const cardTag = document.querySelector(".card-stack__tag");

const exampleCitations = [
    "【1】 quarterly_report.pdf p.4",
    "【2】 employee_handbook.docx p.12",
    "【3】 security_policy.pdf p.2",
    "【4】 onboarding_guide.pdf p.7",
    "【5】 vendor_contract.pdf p.9"
];


function cycleCitationTag() {
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    if (!cardTag || prefersReducedMotion) {
        return; // skip the animation entirely — nothing to clean up
    }

    let index = 0;

    setInterval(function () {
        cardTag.classList.add("is-swapping");

        setTimeout(function () {
            index = (index + 1) % exampleCitations.length;
            cardTag.textContent = exampleCitations[index];
            cardTag.classList.remove("is-swapping");
        }, 300); // matches the CSS transition duration

    }, 2600);
}

cycleCitationTag();



const loginForm = document.getElementById("loginForm");
const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");
const authError = document.getElementById("authError");
const loginBtn = document.getElementById("loginBtn");
const loginBtnText = document.getElementById("loginBtnText");



function showError(message) {
    authError.textContent = message;
    authError.classList.add("is-visible");
}

function clearError() {
    authError.textContent = "";
    authError.classList.remove("is-visible");
}

loginForm.addEventListener("submit" , async function(event){

    event.preventDefault();

    console.log("Login Form Submitted");

    clearError();

    const email = emailInput.value.trim();

    const password = passwordInput.value;

    emailInput.classList.remove("field--invalid");

    passwordInput.classList.remove("field--invalid");


    if (!email && !password) {

        showError("Please enter your email and password.");

        emailInput.classList.add("field--invalid");
        passwordInput.classList.add("field--invalid");

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
    const response = await fetch("/login" , {
        method : "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            email: email,
            password: password
        })
    });

    const data = await response.json();

    if(!response.ok){
        showError(data.detail);
        return;
    }

    console.log("Login successful");

    window.location.href = "/chat-page";
})