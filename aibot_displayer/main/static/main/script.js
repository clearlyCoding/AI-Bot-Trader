$(document).ready(function() {
    // Function to fetch current holdings and historical trades
    function fetchData() {
        $.ajax({
            url: '/api/current_holdings/',  // URL of the Django view
            dataType: 'json',
            success: function(data) {
                // Display current holdings
                displayCurrentHoldings(data.wallet);
                console.log(data.bankmade)
                // Display historical trades
                displayHistoricalTrades(data.bankmade);
            },
            error: function(xhr, status, error) {
                console.error('Error fetching data:', error);
            }
        });
    }

    // Function to display current holdings
    function displayCurrentHoldings(wallet) {
        // Clear previous content
        $('#current-holdings').empty();

        // Iterate over wallet data and display each security
        $.each(wallet, function(security_name, info) {
            $('#current-holdings').append('<p>Security: ' + security_name + ', Total Quantity: ' + info.total_qty + ', Total Cost: ' + info.total_cost + '</p>');
        });
    }

    // Function to display historical trades
    function displayHistoricalTrades(bankmade) {
        // Clear previous content
        $('#historical-trades').empty();

        // Iterate over bankmade data and display each trade
        $.each(bankmade, function(security_name, trades) {
            $.each(trades, function(soldhash, trade) {
                $('#historical-trades').append('<p>Security: ' + trade.security_name + ', Date: ' + trade.date + ', Quantity Sold: ' + trade.qty_sold + ', Sell Price: ' + trade.sell_price + ', Sell Total: ' + trade.sell_total + '</p>');
            });
        });
    }

    // Initial fetch
    fetchData();

    // Set interval to fetch data periodically
    setInterval(fetchData, 1000); // Fetch every 5 seconds
});

/////////////////////WORKS NOW NEED TO MAKE SURE THE UPDATES HAPPEN WHENEVER THE CSV UPDATES - SO UPDATE TO DB - AND ALLOCATE SALES PROPERLY TOO

