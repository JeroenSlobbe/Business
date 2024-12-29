// Add an event listener for industry clicks
document.addEventListener("DOMContentLoaded", function () {
    const industryLinks = document.querySelectorAll(".industry-link");

    industryLinks.forEach(link => {
        link.addEventListener("click", function (event) {
            event.preventDefault(); // Prevent default link behavior

            const industryId = this.dataset.industryId; // Get the industry ID
            fetch(`/stock-seeker/get-stocks?industryId=${industryId}`)
                .then(response => response.json())
                .then(data => {
                    displayStocks(data); // Call a function to update the DOM
                })
                .catch(error => {
                    console.error("Error fetching stocks:", error);
                });
        });
    });
});

// Function to update the DOM with stock data
function displayStocks(stocks) {
    const stocksTableBody = document.getElementById("stocks-table-body");
    stocksTableBody.innerHTML = ""; // Clear previous content

    stocks.forEach(stock => {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${stock.stockId}</td>
            <td>${stock.stockName}</td>
            <td>${stock.price}</td>
        `;
        stocksTableBody.appendChild(row);
    });
}

// Function to fetch stocks for the selected industry
function fetchStocks(industryId) {
    // Make an AJAX request to fetch the stocks for the selected industry
    fetch(`/get_stocks_by_industry_route/${industryId}`)
        .then(response => response.json())
        .then(stocks => {
            // Create HTML for the stock table
            let stockTableHtml = `
                <table>
                    <thead>
                        <tr>
                            <th>Stock Name</th>
                            <th>Ticker</th>
                        </tr>
                    </thead>
                    <tbody>
            `;
            
            // Loop through the stock data and add rows to the table
            stocks.forEach(stock => {
                stockTableHtml += `
                    <tr>
                        <td>${stock.stockname}</td>
                        <td><a href="/stock-seeker/evaluate-stock/${stock.ticker}">${stock.ticker}</a></td>
                    </tr>
                `;
            });
            
            stockTableHtml += '</tbody></table>';
            
            // Add the stock table to the page
            document.getElementById("stock-table-container").innerHTML = stockTableHtml;
        })
        .catch(error => console.error('Error fetching stocks:', error));
}
