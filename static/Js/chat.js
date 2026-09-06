"use strict";


const themeToggle = document.getElementById("themeToggle");
const themeLabel = document.getElementById("themeLabel");
const queryInput = document.getElementById("queryInput")
const composerForm = document.getElementById("composerForm")
const thread = document.getElementById("thread")
const userMessageTemplate = document.getElementById("userMessageTemplate");
const welcomeState = document.getElementById("welcomeState");
const newChatBtn = document.getElementById("newChatBtn");
const convList = document.getElementById("convList");
const convEmpty = document.getElementById("convEmpty");
const conversationTitle = document.getElementById("conversationTitle");
const fileInput = document.getElementById("fileInput");
const uploadStatus = document.getElementById("uploadStatus");
const docList = document.getElementById("docList");
const docEmpty = document.getElementById("docEmpty");
const logoutBtn = document.querySelector(".logout-btn");



let activeConversationId = null

// console.log(queryInput);
// console.log(composerForm);
// console.log(thread);

loadConversations()
restoreLastConversation()
loadDocuments()


themeToggle.addEventListener("click" , function (){

    const currentTheme = document.documentElement.dataset.theme;

    if(currentTheme === "dark"){

        document.documentElement.dataset.theme = "light";

        themeLabel.textContent = "Dark Mode";

    } else{

        document.documentElement.dataset.theme = "dark";

        themeLabel.textContent = "Light Mode";
    }
})


async function loadConversations() {
    const response = await fetch("/conversations");

    const data = await response.json()

    console.log("Conversations:" , data);

    renderConversations(data);

    highlightActiveConversation();
}


function renderConversations(conversations) {

    document.querySelectorAll(".conv-list__item").forEach(function(item) {
        item.remove();
    });

    if (conversations.length === 0) {
        convEmpty.style.display = "block";
        return;
    }

    convEmpty.style.display = "none";

    conversations.forEach(function(conversation) {

        const li = document.createElement("li");

        li.className = "conv-list__item";

        li.dataset.id = conversation.id;


        const titleSpan = document.createElement("span");

        titleSpan.textContent = conversation.title;


        const deleteBtn = document.createElement("button");

        deleteBtn.className = "conv-list__delete";

        deleteBtn.innerHTML = "✕";


        deleteBtn.addEventListener("click" , function(e){

            e.stopPropagation();

            deleteConversation(conversation.id);
        });

        li.appendChild(titleSpan);

        li.appendChild(deleteBtn);


        li.addEventListener("click" , function(){
            loadConversationMessages(
                conversation.id,
                conversation.title
            );
        })

        convList.appendChild(li);

        highlightActiveConversation();

    });
}



async function deleteConversation(id){

    const confirmed = confirm("Delete this conversation? This can't be undone.");

    if(!confirmed){
        return;
    }

    const response = await fetch(`/conversations/${id}`,{
        method : "DELETE"
    });

    if(response.ok){

        if(String(id) === String(activeConversationId)){
            createConversation();
        }
        loadConversations();
    } else{

        console.log("Failed to delete conversation");

    }
}



async function loadConversationMessages(id , title){

    activeConversationId = id;

    localStorage.setItem("archivist-active-conversation", id);

    highlightActiveConversation();

    document.getElementById("conversationTitle").textContent = title;

    console.log("Loading conversation:", id);

    const response = await fetch(
        `/conversations/${id}/messages`
    );

    const messages = await response.json()

    console.log("Messages:", messages);

    thread.querySelectorAll(".msg").forEach(function(message){

        message.remove();
    })

    welcomeState.style.display = "none";

    messages.forEach(function(message){

        if(message.role == "user"){

            showUserMessage(message.content)

        }else if(message.role == "assistant"){

            showAssistantMessage(message.content , message.citations || []);

        }
    });

}


async function restoreLastConversation(){

    const saveId = localStorage.getItem("archivist-active-conversation");

    if(!saveId){
        return
    }

    const response = await fetch("/conversations");

    const conversations = await response.json()

    const match =
        conversations.find(function(c) {

            return String(c.id) === saveId;

        });
    
    if(match){

        loadConversationMessages(
            match.id,
            match.title
        );
    } else{

        localStorage.removeItem(
            "archivist-active-conversation"
        );
    }
    
}


function showAssistantMessage(text , sources){
    const template = document.getElementById("assistantMessageTemplate");

    const message = template.content.cloneNode(true)

    message.querySelector(".msg__bubble").textContent = text;

    const citations = message.querySelector(".citations");

    sources.forEach(function(source){
        const citation = document.createElement("span")

        citation.className = "citation-tag";

        citation.textContent =
            `[${source.number}] ${source.source} p.${source.page}`;

        citations.appendChild(citation);
    })

    thread.appendChild(message);
}


function showUserMessage(text){

    const message = userMessageTemplate.content.cloneNode(true);

    message.querySelector(".msg__bubble").textContent = text;

    thread.appendChild(message)
}


function createConversation() {

    activeConversationId = null;

    highlightActiveConversation();

    localStorage.removeItem("archivist-active-conversation");

    thread.querySelectorAll(".msg").forEach(function(message) {
        message.remove();
    });

    welcomeState.style.display = "block";

    document.getElementById("conversationTitle").textContent = "Select or start a conversation";

    document.getElementById("conversationSubtitle").textContent = "Answers are grounded only in your indexed documents.";


    console.log("New conversation started");

}


function showTyping() {
    const template = document.getElementById("typingTemplate");
    const indicator = template.content.cloneNode(true);
    thread.appendChild(indicator);
}


function hideTyping() {
    const indicator = document.getElementById("typingIndicator");
    if (indicator) {
        indicator.remove();
    }
}

newChatBtn.addEventListener("click", createConversation);



composerForm.addEventListener("submit" , async function(event){
    event.preventDefault();

    console.log("Form submitted")

    const query = queryInput.value.trim();

    if(!query){
        return
    }

    queryInput.value = "";

    welcomeState.style.display = "none";

    showUserMessage(query);
    
    showTyping();

    const response = await fetch("/chat", {
        method : "POST",
        headers: {
        "Content-Type": "application/json"
        },
        body: JSON.stringify({
            query: query,
            conversation_id : activeConversationId
        })
    });

    hideTyping();

    console.log(response);

    const data = await response.json();

    if (!response.ok) {

        console.log("Chat request failed:", data);

        return;
    }

    activeConversationId = data.conversation_id;

    conversationTitle.textContent = data.title;

    localStorage.setItem("archivist-active-conversation", activeConversationId); 

    highlightActiveConversation();

    console.log("Conversation ID:", activeConversationId);

    showAssistantMessage(data.answer , data.sources || []);

    loadConversations();

});

composerForm.addEventListener("keydown" , function(event){

    if(event.key == "Enter" && !event.shiftKey){

        event.preventDefault();

        composerForm.requestSubmit();

    }
});


function highlightActiveConversation(){

    document.querySelectorAll(".conv-list__item").forEach(function (item){

        item.classList.toggle(
            "is-active",
            item.dataset.id === String(activeConversationId)
        );
    });
}


fileInput.addEventListener("change" , uploadFile);

async function uploadFile(){

    const file = fileInput.files[0];

    if(!file){
        return;
    }

    console.log("Selected file:", file.name);

    uploadStatus.textContent = "uploading...";

    const formData = new FormData();

    formData.append("file" , file);

    try{

        const response = await fetch("/upload",{
            method : "POST",
            body : formData
        });

        const data = await response.json();

        console.log("Upload response:", data);

        if (!response.ok) {
            uploadStatus.textContent =
                data.detail || data.message || "Upload failed";
            return;
        }

        uploadStatus.textContent = data.message;

    } catch(error){
        
        console.error("Upload error:", error);

        uploadStatus.textContent = "Something went wrong";

    }

    fileInput.value = "";

    loadDocuments();
}


async function loadDocuments(){

    const response = await fetch("/documents");

    const data = await response.json();

    console.log("Documents:", data);

    renderDocuments(data);
}

function renderDocuments(documents){

    docList.innerHTML = "";

    if(documents.length === 0){
        docEmpty.style.display = "block";
        docList.appendChild(docEmpty);
        return;
    }

    docEmpty.style.display = "none";

    documents.forEach(function(doc){

        const li = document.createElement("li");

        li.className = "doc-list__item";

        li.innerHTML = `
            <span class="doc-list__name">
                ${doc.filename}
            </span>
            <button class="doc-list__delete">✕</button>
        `;

        const deleteBtn = li.querySelector(".doc-list__delete");

        deleteBtn.addEventListener("click" , function(){

            deleteDocument(doc.id);

        });

        docList.appendChild(li);
    });
}


async function deleteDocument(id){

    const confirmed = confirm("Delete this document? This can't be undone.");

    if(!confirmed){
        return;
    }

    const response = await fetch(`/documents/${id}`,{
        method : "DELETE"
    });

    if(response.ok){

        loadDocuments();

    } else{

        const data = await response.json().catch(() => ({}));

        alert(data.detail || "Failed to delete document.");

    }
}


logoutBtn.addEventListener("click" , async function(){

    const response = await fetch("/logout" , {
        method : "POST"
    });

    if(response.ok){

        window.location.href = "/login";

    }

});
