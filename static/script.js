document.addEventListener("DOMContentLoaded", function() {
    const form = document.getElementById("postItemForm");
    const itemsFeed = document.getElementById("itemsFeed");
    const postMessage = document.getElementById("postMessage");

    const apiBaseUrl = "http://localhost:5000/api";  // Your Flask API base URL

    // Handle form submission
    form.addEventListener("submit", function(event) {
        event.preventDefault();

        const formData = new FormData(form);
        postItem(formData);
    });

    // Post new item to the API
    function postItem(formData) {
        fetch(`${apiBaseUrl}/items`, {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            postMessage.textContent = data.message;
            form.reset();
            loadItems();  // Reload feed after posting new item
        })
        .catch(error => {
            console.error("Error posting item:", error);
            postMessage.textContent = "Failed to post item.";
        });
    }

    // Load items feed from the API
    function loadItems(filters = {}) {
        let url = `${apiBaseUrl}/items`;

        const queryParams = new URLSearchParams(filters).toString();
        if (queryParams) {
            url += `?${queryParams}`;
        }

        fetch(url)
        .then(response => response.json())
        .then(data => {
            itemsFeed.innerHTML = "";  // Clear current feed
            data.forEach(item => {
                const itemDiv = document.createElement("div");
                itemDiv.className = "item";
                itemDiv.innerHTML = `
                    <img src="${item.image_url}" alt="${item.title}">
                    <h3>${item.title}</h3>
                    <p>${item.description}</p>
                    <p><strong>Category:</strong> ${item.category}</p>
                    <p><strong>Status:</strong> ${item.status}</p>
                    <p><strong>Location:</strong> ${item.location}</p>
                `;
                itemsFeed.appendChild(itemDiv);
            });
        })
        .catch(error => {
            console.error("Error loading items:", error);
        });
    }

    // Apply filters to the item feed
    document.getElementById("applyFilters").addEventListener("click", function() {
        const status = document.getElementById("filterStatus").value;
        const category = document.getElementById("filterCategory").value;

        const filters = {};
        if (status) filters.status = status;
        if (category) filters.category = category;

        loadItems(filters);
    });

    // Initial load of items
    loadItems();
});
